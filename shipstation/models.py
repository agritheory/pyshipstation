from shipstation.constants import *
from decimal import Decimal
import datetime
import json
import re
from requests import Response

__all__ = [
    "ShipStationAddress",
    "ShipStationAdvancedOptions",
    "ShipStationBase",
    "ShipStationCarrier",
    "ShipStationCarrierPackage",
    "ShipStationCarrierService",
    "ShipStationContainer",
    "ShipStationCustomsItem",
    "ShipStationCustomer",
    "ShipStationHTTP",
    "ShipStationInsuranceOptions",
    "ShipStationInternationalOptions",
    "ShipStationItem",
    "ShipStationMarketplace",
    "ShipStationOrder",
    "ShipStationStatusMapping",
    "ShipStationStore",
    "ShipStationUser",
    "ShipStationWarehouse",
    "ShipStationWebhook",
    "ShipStationWeight",
]

snake_case_regex = re.compile("([a-z0-9])([A-Z])")


class ShipStationBase(object):
    @classmethod
    def to_camel_case(cls, name):
        tokens = name.lower().split("_")
        first_word = tokens.pop(0)
        return first_word + "".join(x.title() for x in tokens)

    @classmethod
    def to_snake_case(cls, name):
        return snake_case_regex.sub(r"\1_\2", name).lower()

    def as_dict(self):
        if self.__dict__:
            return {
                self.to_camel_case(key): value for key, value in self.__dict__.items()
            }
        elif self.__slots__:
            return {
                self.to_camel_case(key): self.__getattribute__(key)
                for key in self.__slots__
            }

    def require_attribute(self, attribute):
        if not getattr(self, attribute):
            raise AttributeError("'{}' is a required attribute".format(attribute))

    def require_type(self, item, required_type, message=""):
        if item is None:
            return
        if not isinstance(item, required_type):
            if message:
                raise AttributeError(message)
            raise AttributeError("must be of type {}".format(required_type))

    def require_membership(self, value, other):
        if value not in other:
            raise AttributeError("'{}' is not one of {}".format(value, str(other)))

    def _validate_parameters(self, parameters, valid_parameters):
        self.require_type(parameters, dict)
        return {self.to_camel_case(key): value for key, value in parameters.items()}

    def from_json(self, json_str):
        if isinstance(json_str, Response):
            s = json_str.json()
        elif isinstance(json_str, str):
            s = json.loads(json_str)
        else:
            s = json_str  # allow dict to pass
        for key, value in s.items():
            setattr(self, self.to_snake_case(key), value)
        return self

    def json(self):
        j = self.as_dict()
        for key, value in j.items():
            if isinstance(value, bool):
                j[key] = "true" if value else "false"
            elif isinstance(value, (int, float, Decimal)):
                j[key] = str(value)
            elif isinstance(value, type) and value.__class__.split(".")[-1] in __all__:
                j[key] = value.json()
        return json.dumps(j)

    def object_list(self, r, object_type):
        if isinstance(r, list):  # already a list of json/objects
            return [object_type().from_json(obj) for obj in r]
        r = r.json()
        r = [r] if isinstance(r, dict) else r
        return [object_type().from_json(obj) for obj in r]


class ShipStationHTTP(ShipStationBase):
    def get(self, endpoint="", payload=None):
        url = "{}{}".format(self.url, endpoint)
        r = requests.get(
            url, auth=(self.key, self.secret), params=payload, timeout=self.timeout
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint("GET " + url)
            pprint.PrettyPrinter(indent=4).pprint(r.json())

        return r

    def post(self, endpoint="", data=None):
        url = "{}{}".format(self.url, endpoint)
        headers = {"content-type": "application/json"}
        r = requests.post(
            url,
            auth=(self.key, self.secret),
            data=data,
            headers=headers,
            timeout=self.timeout,
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint(r.json())

        return r

    def put(self, endpoint="", data=None):
        url = "{}{}".format(self.url, endpoint)
        headers = {"content-type": "application/json"}
        r = requests.put(
            url,
            auth=(self.key, self.secret),
            data=data,
            headers=headers,
            timeout=self.timeout,
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint("PUT " + url)
            pprint.PrettyPrinter(indent=4).pprint(r.json())

        return r

    def delete(self, endpoint="", payload=None):
        url = "{}{}".format(self.url, endpoint)
        r = requests.delete(
            url, auth=(self.key, self.secret), params=payload, timeout=self.timeout
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint("DELETE " + url)
            pprint.PrettyPrinter(indent=4).pprint(r)

        return r


class ShipStationCustomsItem(ShipStationBase):
    def __init__(
        self,
        description=None,
        quantity=1,
        value=Decimal("0"),
        harmonized_tariff_code=None,
        country_of_origin=None,
    ):
        self.description = description
        self.quantity = quantity
        self.value = value
        self.harmonized_tariff_code = harmonized_tariff_code
        self.country_of_origin = country_of_origin

        self.require_attribute("description")
        self.require_attribute("harmonized_tariff_code")
        self.require_attribute("country_of_origin")
        self.require_attribute("description")
        self.require_type(value, Decimal)
        if len(self.country_of_origin) is not 2:
            raise AttributeError("country_of_origin must be two characters")


class ShipStationInternationalOptions(ShipStationBase):
    def __init__(self, contents=None, non_delivery="return_to_sender"):
        self.customs_items = []
        self.set_contents(contents)
        self.set_non_delivery(non_delivery)

    def set_contents(self, contents):
        if contents:
            if contents not in CONTENTS_VALUES:
                raise AttributeError("contents value not valid")
            self.contents = contents
        else:
            self.contents = None

    def add_customs_item(self, customs_item):
        self.require_type(customs_item, ShipStationCustomsItem)
        self.customs_items.append(customs_item)

    def get_items(self):
        return self.customs_items

    def get_items_as_dicts(self):
        return [x.as_dict() for x in self.customs_items]

    def set_non_delivery(self, non_delivery):
        if non_delivery:
            if non_delivery not in NON_DELIVERY_OPTIONS:
                raise AttributeError("non_delivery value is not valid")
            self.non_delivery = non_delivery
        else:
            self.non_delivery = None

    def as_dict(self):
        d = super(ShipStationInternationalOptions, self).as_dict()
        d["customsItems"] = self.get_items_as_dicts()
        return d


class ShipStationWeight(ShipStationBase):
    __slots__ = ["units", "value", "WeightUnits"]

    def __init__(self, units=None, value=None):
        self.units = units
        self.value = value
        self.WeightUnits = None

    def get_units(self):
        return self.WeightUnits

    def set_units(self):
        self.require_membership(self.units, WEIGHT_UNIT_OPTIONS)
        self.WeightUnits = self.units

    def as_dict(self):
        return {"value": self.value, "units": self.WeightUnits}


class ShipStationContainer(ShipStationBase):
    def __init__(self, units=None, length=None, width=None, height=None):
        self.units = units
        self.length = length
        self.width = width
        self.height = height
        self.weight = None

    def set_weight(self, weight):
        self.require_type(weight, ShipStationWeight)
        self.weight = weight

    def set_units(self, units):
        # WEIGHT_UNIT_OPTIONS
        self.require_membership(units, WEIGHT_UNIT_OPTIONS)
        self.units = units

    def as_dict(self):
        d = super(ShipStationContainer, self).as_dict()
        return __setattr__(d, "weight", self.weight.as_dict()) if self.weight else d


class ShipStationItem(ShipStationBase):
    def __init__(
        self,
        key=None,
        sku=None,
        name=None,
        image_url=None,
        quantity=None,
        unit_price=None,
        warehouse_location=None,
        options=None,
    ):
        self.key = key
        self.sku = sku
        self.name = name
        self.image_url = image_url
        self.weight = None
        self.quantity = quantity
        self.unit_price = unit_price
        self.warehouse_location = warehouse_location
        self.options = options

    def set_weight(self, weight):
        self.require_type(weight, ShipStationWeight)
        self.weight = weight

    def as_dict(self):
        d = super(ShipStationItem, self).as_dict()
        return __setattr__(d, "weight", self.weight.as_dict()) if self.weight else d


class ShipStationAddress(ShipStationBase):
    __slots__ = [
        "name",
        "company",
        "street1",
        "street2",
        "street3",
        "city",
        "state",
        "postal_code",
        "country",
        "phone",
        "residential",
    ]

    def __init__(
        self,
        name=None,
        company=None,
        street1=None,
        street2=None,
        street3=None,
        city=None,
        state=None,
        postal_code=None,
        country=None,
        phone=None,
        residential=None,
    ):
        self.name = name
        self.company = company
        self.street1 = street1
        self.street2 = street2
        self.street3 = street3
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
        self.phone = phone
        self.residential = residential


class ShipStationOrder(ShipStationBase):
    """
    Accepts the data needed for an individual ShipStation order and
    contains the tools for submitting the order to ShipStation.
    """

    __slots__ = [
        "advanced_options",
        "amount_paid",
        "batch_number",
        "bill_to",
        "carrier_code",
        "confirmation",
        "create_date",
        "customer_email",
        "customer_notes",
        "customer_username",
        "dimensions",
        "form_data",
        "gift",
        "insurance_cost",
        "insurance_options",
        "internal_notes",
        "international_options",
        "is_return_label",
        "items",
        "label_data",
        "marketplace_notified",
        "notify_error_message",
        "order_date",
        "order_id",
        "order_key",
        "order_number",
        "order_status",
        "package_code",
        "payment_date",
        "payment_method",
        "service_code",
        "ship_date",
        "ship_to",
        "shipment_cost",
        "shipment_id",
        "shipment_items",
        "shipping_amount",
        "tax_amount",
        "tracking_number",
        "user_id",
        "void_date",
        "voided",
        "warehouse_id",
        "weight",
    ]

    def __init__(self, order_key=None, order_number=None):

        # Required attributes
        self.order_number = order_number
        self.order_date = datetime.datetime.now().isoformat()
        self.order_status = None
        self.bill_to = None
        self.ship_to = None

        # Optional attributes
        self.order_key = order_key
        self.payment_date = None
        self.customer_username = None
        self.customer_email = None
        self.items = []
        self.amount_paid = Decimal("0")
        self.tax_amount = Decimal("0")
        self.shipping_amount = Decimal("0")
        self.customer_notes = None
        self.internal_notes = None
        self.gift = None
        self.payment_method = None
        self.carrier_code = None
        self.service_code = None
        self.package_code = None
        self.confirmation = None
        self.ship_date = None
        self.dimensions = None
        self.insurance_options = None
        self.international_options = None
        self.advanced_options = None

        self.tracking_number = None
        self.voided = None
        self.void_date = None
        self.order_id = None
        self.marketplace_notified = None
        self.warehouse_id = None
        self.user_id = None
        self.label_data = None
        self.batch_number = None
        self.insurance_cost = None
        self.form_data = None
        self.notify_error_message = None
        self.is_return_label = None
        self.shipment_id = None
        self.shipment_cost = None
        self.weight = None
        self.create_date = None
        self.shipment_items = None

    def set_status(self, status=None):
        if not status:
            self.order_status = None
        elif status not in ORDER_STATUS_VALUES:
            raise AttributeError("Invalid status value")
        else:
            self.order_status = status

    def set_customer_details(self, username=None, email=None):
        self.customer_username = username
        self.customer_email = email

    def set_shipping_address(self, shipping_address=None):
        self.require_type(shipping_address, ShipStationAddress)
        self.ship_to = shipping_address

    def get_shipping_address_as_dict(self):
        return self.ship_to.as_dict() if self.ship_to else None

    def set_billing_address(self, billing_address):
        self.require_type(billing_address, ShipStationAddress)
        self.bill_to = billing_address

    def get_billing_address_as_dict(self):
        return self.bill_to.as_dict() if self.bill_to else None

    def set_dimensions(self, dimensions):
        self.require_type(dimensions, ShipStationContainer)
        self.dimensions = dimensions

    def get_dimensions_as_dict(self):
        return self.dimensions.as_dict() if self.dimensions else None

    def set_order_date(self, date):
        self.order_date = date

    def get_order_date(self):
        return self.order_date

    def get_weight(self):
        weight = 0
        items = self.get_items()
        weight = sum([item.weight.value * item.quantity for item in items])
        if self.dimensions and self.dimensions.weight:
            weight += self.dimensions.weight.value

        return dict(units="ounces", value=round(weight, 2))

    def add_item(self, item):
        """
        Adds a new item to the order with all of the required keys.
        """
        self.items.append(item)

    def get_items(self):
        return self.items

    def get_items_as_dicts(self):
        return [x.as_dict() for x in self.items]

    def set_international_options(self, options):
        self.require_type(options, ShipStationInternationalOptions)
        self.international_options = options

    def get_international_options_as_dict(self):
        return (
            self.international_options.as_dict() if self.international_options else None
        )

    def as_dict(self):
        d = super(ShipStationOrder, self).as_dict()
        d["items"] = self.get_items_as_dicts()
        d["dimensions"] = self.get_dimensions_as_dict()
        d["billTo"] = self.get_billing_address_as_dict()
        d["shipTo"] = self.get_shipping_address_as_dict()
        d["weight"] = self.get_weight()
        d["internationalOptions"] = self.get_international_options_as_dict()
        return d

    def json(self):
        return json.dumps(self.as_dict())


class ShipStationAdvancedOptions(ShipStationBase):
    def __init__(
        self,
        warehouse_id=None,
        non_machineable=None,
        saturday_delivery=None,
        contains_alcohol=None,
        store_id=None,
        custom_field_1=None,
        custom_field_2=None,
        custom_field_3=None,
        source=None,
        merged_or_split=None,
        merged_ids=None,
        bill_to_party=None,
        bill_to_account=None,
        bill_to_postal_code=None,
        bill_to_country_code=None,
        bill_to_my_other_account=None,
    ):
        self.warehouse_id = warehouse_id
        self.non_machineable = non_machineable
        self.saturday_delivery = saturday_delivery
        self.contains_alcohol = contains_alcohol
        self.store_id = store_id
        self.custom_field_1 = custom_field_1
        self.custom_field_2 = custom_field_2
        self.custom_field_3 = custom_field_3
        self.source = source
        self.merged_or_split = merged_or_split
        self.merged_ids = merged_ids
        self.bill_to_party = bill_to_party
        self.bill_to_account = bill_to_account
        self.bill_to_postal_code = bill_to_postal_code
        self.bill_to_country_code = bill_to_country_code
        self.bill_to_my_other_account = bill_to_my_other_account


class ShipStationInsuranceOptions(ShipStationBase):
    def __init__(self, provider=None, insure_shipment=None, insured_value=None):
        self.provider = provider
        self.insure_shipment = insure_shipment
        self.insured_value = insured_value


class ShipStationStatusMapping(ShipStationBase):
    def __init__(self, order_status=None, status_key=None):
        self.order_status = order_status
        self.status_key = status_key


class ShipStationStore(ShipStationBase):
    __slots__ = [
        "store_id",
        "store_name",
        "marketplace_id",
        "marketplace_name",
        "account_name",
        "email",
        "integration_url",
        "active",
        "company_name",
        "phone",
        "public_email",
        "website",
        "refresh_date",
        "last_refresh_attempt",
        "create_date",
        "modify_date",
        "auto_refresh",
        "status_mappings",
    ]

    def __init__(
        self,
        store_id=None,
        store_name=None,
        marketplace_id=None,
        marketplace_name=None,
        account_name=None,
        email=None,
        integration_url=None,
        active=None,
        company_name=None,
        phone=None,
        public_email=None,
        website=None,
        refresh_date=None,
        last_refresh_attempt=None,
        create_date=None,
        modify_date=None,
        auto_refresh=None,
        status_mappings=None,
    ):
        self.store_id = store_id
        self.store_name = store_name
        self.marketplace_id = marketplace_id
        self.marketplace_name = marketplace_name
        self.account_name = account_name
        self.email = email
        self.integration_url = integration_url
        self.active = active
        self.company_name = company_name
        self.phone = phone
        self.public_email = public_email
        self.website = website
        self.refresh_date = refresh_date
        self.last_refresh_attempt = last_refresh_attempt
        self.create_date = create_date
        self.modify_date = modify_date
        self.auto_refresh = auto_refresh
        self.status_mappings = status_mappings


class ShipStationWarehouse(ShipStationBase):
    __slots__ = [
        "create_date",
        "ext_inventory_identity",
        "is_default",
        "origin_address",
        "return_address",
        "register_fedex_meter",
        "seller_integration_id",
        "warehouse_id",
        "warehouse_name",
    ]

    def __init__(
        self,
        create_date=None,
        ext_inventory_identity=None,
        is_default=None,
        origin_address=None,
        return_address=None,
        register_fedex_meter=None,
        seller_integration_id=None,
        warehouse_id=None,
        warehouse_name=None,
    ):
        self.create_date = create_date
        self.ext_inventory_identity = ext_inventory_identity
        self.is_default = is_default
        self.origin_address = origin_address
        self.return_address = return_address
        self.register_fedex_meter = register_fedex_meter
        self.seller_integration_id = seller_integration_id
        self.warehouse_id = warehouse_id
        self.warehouse_name = warehouse_name

    def as_dict(self):
        d = super(ShipStationWarehouse, self).as_dict()
        if self.origin_address:
            d["originAddress"] = self.origin_address.as_dict()
        if self.return_address:
            d["returnAddress"] = self.return_address.as_dict()
        return d

    def from_json(self, json_str):
        d = super(ShipStationWarehouse, self).from_json(json_str)
        if d.origin_address:
            d.origin_address = ShipStationAddress().from_json(d.origin_address)
        if d.return_address:
            d.return_address = ShipStationAddress().from_json(d.return_address)
        return d


class ShipStationWebhook(ShipStationBase):
    __slots__ = [
        "active",
        "is_label_apihook",
        "web_hook_id",
        "seller_id",
        "hook_type",
        "message_format",
        "url",
        "name",
        "bulk_copy_batch_id",
        "bulk_copy_record_id",
        "webhook_logs",
        "seller",
        "store",
        "store_id",
    ]

    def __init__(
        self,
        active=None,
        is_label_apihook=None,
        web_hook_id=None,
        seller_id=None,
        hook_type=None,
        message_format=None,
        url=None,
        name=None,
        bulk_copy_batch_id=None,
        bulk_copy_record_id=None,
        webhook_logs=None,
        seller=None,
        store_id=None,
        store=None,
    ):
        self.active = active
        self.is_label_apihook = is_label_apihook
        self.web_hook_id = web_hook_id
        self.seller_id = seller_id
        self.hook_type = hook_type
        self.message_format = message_format
        self.url = url
        self.name = name
        self.bulk_copy_batch_id = bulk_copy_batch_id
        self.bulk_copy_record_id = bulk_copy_record_id
        self.webhook_logs = webhook_logs
        self.seller = seller
        self.store_id = store_id


class ShipStationUser(ShipStationBase):
    __slots__ = ["name", "user_id", "user_name"]

    def __init__(self, name=None, user_id=None, user_name=None):
        self.name = name
        self.user_id = user_id
        self.user_name = user_name


class ShipStationMarketplace(ShipStationBase):
    __slots__ = [
        "can_confirm_shipments",
        "can_refresh",
        "marketplace_id",
        "name",
        "supports_custom_mappings",
        "supports_custom_statuses",
    ]

    def __init__(
        self,
        can_confirm_shipments=None,
        can_refresh=None,
        marketplace_id=None,
        name=None,
        supports_custom_mappings=None,
        supports_custom_statuses=None,
    ):
        self.can_confirm_shipments = can_confirm_shipments
        self.can_refresh = can_refresh
        self.marketplace_id = marketplace_id
        self.name = name
        self.supports_custom_mappings = supports_custom_mappings
        self.supports_custom_statuses = supports_custom_statuses


class ShipStationCustomer(ShipStationBase):
    __slots__ = [
        "address_verified",
        "city",
        "company",
        "country_code",
        "create_date",
        "customer_id",
        "email",
        "marketplace_usernames",
        "modify_date",
        "name",
        "phone",
        "postal_code",
        "state",
        "street1",
        "street2",
        "tags",
    ]

    def __init__(
        self,
        address_verified=None,
        city=None,
        company=None,
        country_code=None,
        create_date=None,
        customer_id=None,
        email=None,
        marketplace_usernames=None,
        modify_date=None,
        name=None,
        phone=None,
        postal_code=None,
        state=None,
        street1=None,
        street2=None,
        tags=None,
    ):
        self.address_verified = address_verified
        self.city = city
        self.company = company
        self.country_code = country_code
        self.create_date = create_date
        self.customer_id = customer_id
        self.email = email
        self.marketplace_usernames = marketplace_usernames
        self.modify_date = modify_date
        self.name = name
        self.phone = phone
        self.postal_code = postal_code
        self.state = state
        self.street1 = street1
        self.street2 = street2
        self.tags = tags

    def as_dict(self):
        d = super(ShipStationCustomer, self).as_dict()
        if self.marketplace_usernames:
            [
                d["marketplaceUsernames"].append(i.as_dict())
                for i in self.marketplace_usernames
            ]
        return d

    def from_json(self, json_str):
        d = super(ShipStationCustomer, self).from_json(json_str)
        marketplace_usernames = []
        if d.marketplace_usernames:
            [
                marketplace_usernames.append(
                    ShipStationMarketplaceUsername().from_json(i)
                )
                for i in d.marketplace_usernames
            ]
            d.marketplace_usernames = marketplace_usernames
        return d


class ShipStationMarketplaceUsername(ShipStationBase):
    __slots__ = [
        "create_date",
        "customer_id",
        "customer_user_id",
        "marketplace",
        "marketplace_id",
        "modify_date",
        "username",
    ]

    def __init__(
        self,
        create_date=None,
        customer_id=None,
        customer_user_id=None,
        marketplace=None,
        marketplace_id=None,
        modify_date=None,
        username=None,
    ):
        self.create_date = create_date
        self.customer_id = customer_id
        self.customer_user_id = customer_user_id
        self.marketplace = marketplace
        self.marketplace_id = marketplace_id
        self.modify_date = modify_date
        self.username = username


class ShipStationCarrier(ShipStationBase):
    __slots__ = [
        "account_number",
        "balance",
        "code",
        "name",
        "nickname",
        "primary",
        "requires_funded_account",
        "shipping_provider_id",
    ]

    def __init__(
        self,
        account_number=None,
        balance=None,
        code=None,
        name=None,
        nickname=None,
        primary=None,
        requires_funded_account=None,
        shipping_provider_id=None,
    ):
        self.account_number = account_number
        self.balance = balance
        self.code = code
        self.name = name
        self.nickname = nickname
        self.primary = primary
        self.requires_funded_account = requires_funded_account
        self.shipping_provider_id = shipping_provider_id


class ShipStationCarrierPackage(ShipStationBase):
    __slots__ = ["carrier_code", "code", "domestic", "international", "name"]

    def __init__(
        self, carrier_code=None, code=None, domestic=None, international=None, name=None
    ):
        self.carrier_code = carrier_code
        self.code = code
        self.domestic = domestic
        self.international = international
        self.name = name


class ShipStationCarrierService(ShipStationCarrierPackage):
    pass
