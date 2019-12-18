import datetime
from decimal import Decimal
import json
import pprint
import httpx
from shipstation.models import *
from shipstation.constants import *


class ShipStationAsync(ShipStationBase):
    async def get(self, endpoint="", payload=None):
        url = "{}{}".format(self.url, endpoint)
        r = await httpx.get(
            url, auth=(self.key, self.secret), params=payload, timeout=self.timeout
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint("GET " + url)
            pprint.PrettyPrinter(indent=4).pprint(r.json())

        return r

    async def post(self, endpoint="", data=None):
        url = "{}{}".format(self.url, endpoint)
        headers = {"content-type": "application/json"}
        r = await httpx.post(
            url,
            auth=(self.key, self.secret),
            data=data,
            headers=headers,
            timeout=self.timeout,
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint(r.json())

        return r

    async def put(self, endpoint="", data=None):
        url = "{}{}".format(self.url, endpoint)
        headers = {"content-type": "application/json"}
        r = await httpx.put(
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

    async def delete(self, endpoint="", payload=None):
        url = "{}{}".format(self.url, endpoint)
        r = await httpx.delete(
            url, auth=(self.key, self.secret), params=payload, timeout=self.timeout
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint("DELETE " + url)
            pprint.PrettyPrinter(indent=4).pprint(r)

        return r


class ShipStation(ShipStationAsync):
    """
    Handles the details of connecting to and querying a ShipStation account.
    """

    def __init__(self, key=None, secret=None, debug=False, timeout=1):
        """
        Connecting to ShipStation required an account and a
        :return:
        """

        if key is None:
            raise AttributeError("Key must be supplied.")
        if secret is None:
            raise AttributeError("Secret must be supplied.")

        self.url = "https://ssapi.shipstation.com"

        self.key = key
        self.secret = secret
        self.orders = []
        self.timeout = timeout
        self.debug = debug

    def add_order(self, order):
        self.require_type(order, ShipStationOrder)
        self.orders.append(order)

    def get_orders(self):
        return self.orders

    def submit_orders(self):
        for order in self.orders:
            self.post(endpoint="/orders/createorder", data=json.dumps(order.as_dict()))

    def fetch_orders(self, parameters={}):
        """
            Query, fetch, and return existing orders from ShipStation

            Args:
                parameters (dict): Dict of filters to filter by.

            Raises:
                AttributeError: parameters not of type dict
                AttributeError: invalid key in parameters dict.

            Returns:
                A <Response [code]> object.

            Examples:
                >>> ss.fetch_orders(parameters={'order_status': 'shipped', 'page': '2'})
        """
        self.require_type(parameters, dict)
        invalid_keys = set(parameters.keys()).difference(ORDER_LIST_PARAMETERS)
        if invalid_keys:
            raise AttributeError(
                "Invalid order list parameters: {}".format(", ".join(invalid_keys))
            )

        valid_parameters = {
            self.to_camel_case(key): value for key, value in parameters.items()
        }

        return self.get(endpoint="/orders/list", payload=valid_parameters)

    async def list_carriers(self):
        return await self.get(endpoint="/carriers/")

    async def get_carrier(self, carrier_code):
        carrier = await self.get(
            endpoint="/carriers/getcarrier", payload={"carrierCode": carrier_code}
        )
        return ShipStationCarrier().from_json(carrier.json())

    async def list_packages(self, carrier_code):
        packages = await self.get(
            endpoint="/carriers/listpackages", payload={"carrierCode": carrier_code}
        )
        return self.object_list(packages.json(), ShipStationCarrierPackage)

    async def list_services(self, carrier_code):
        services = await self.get(
            endpoint="/carriers/listservices", payload={"carrierCode": carrier_code}
        )
        return self.object_list(services.json(), ShipStationCarrierService)

    def get_customer(self, customer_id):
        return ShipStationCustomer().from_json(
            self.get(endpoint="/customers/" + str(customer_id))
        )

    def list_customers(self, parameters={}):
        valid_parameters = self._validate_parameters(
            parameters, CUSTOMER_LIST_PARAMETERS
        )
        r = self.get(endpoint="/customers", payload=valid_parameters)
        customer_list = r.json().get("customers")
        return [ShipStationCustomer().from_json(c) for c in customer_list]

    # TODO: return list of fulfillments as objects
    def list_fulfillments(self, parameters={}):
        valid_parameters = self._validate_parameters(
            parameters, FULFILLMENT_LIST_PARAMETERS
        )
        return self.get(endpoint="/fulfillments", payload=valid_parameters)

    def list_shipments(self, parameters={}):
        valid_parameters = self._validate_parameters(
            parameters, SHIPMENT_LIST_PARAMETERS
        )
        r = self.get(endpoint="/shipments", payload=valid_parameters)
        shipments = r.json().get("shipments")
        return [ShipStationOrder().from_json(s) for s in shipments]

    # TODO: return shipment label as objects
    def create_shipment_label(self, options):
        valid_options = self._validate_parameters(
            options, CREATE_SHIPMENT_LABEL_OPTIONS
        )
        self.require_type(options.get("weight"), ShipStationWeight)
        self.require_type(options.get("dimensions"), ShipStationContainer)
        self.require_type(options.get("ship_to"), ShipStationAddress)
        self.require_type(options.get("ship_from"), ShipStationAddress)
        self.require_type(
            options.get("international_options"), ShipStationInternationalOptions
        )
        self.require_type(options.get("advanced_options"), ShipStationAdvancedOptions)
        return self.post(endpoint="/shipments/createlabel", data=valid_options)

    # TODO: return list of rates as objects
    def get_rates(self, options):
        self.require_type(options.get("weight"), ShipStationWeight)
        self.require_type(options.get("dimensions"), ShipStationContainer)
        valid_options = self._validate_parameters(options, GET_RATE_OPTIONS)
        for required_option in REQUIRED_RATE_OPTIONS:
            if not options.get(required_option):
                raise AttributeError(
                    "'{}' is required to get rates".format(required_option)
                )
        return self.post(endpoint="/shipments/getrates", data=valid_options)

    # TODO: return status code
    def void_label(self, shipment_id):
        return self.post(endpoint="/shipments/voidlabel", data=shipment_id)

    def list_marketplaces(self):
        return self.object_list(
            self.get(endpoint="/stores/marketplaces/"), ShipStationMarketplace
        )

    def list_stores(self, show_inactive=False, marketplace_id=None):
        self.require_type(show_inactive, bool)
        self.require_type(marketplace_id, int)
        parameters = {}
        if show_inactive:
            parameters["showInactive"] = show_inactive
        if marketplace_id:
            parameters["marketplaceId"] = marketplace_id
        return self.object_list(
            self.get(endpoint="/stores", payload=parameters), ShipStationStore
        )

    def get_store(self, store_id):
        store = self.get(endpoint="/stores/" + str(store_id))
        return ShipStationStore().from_json(store)

    def update_store(self, options):
        options = self._validate_parameters(options, UPDATE_STORE_OPTIONS)
        [self.require_attribute(m) for m in UPDATE_STORE_OPTIONS]
        self.require_type(options.get("status_mappings"), list)
        for mapping in status_mappings:
            self.require_type(mapping, ShipStationStatusMapping)
            self.require_membership(mapping["orderStatus"], ORDER_STATUS_VALUES)
        store = self.put(endpoint="/stores/storeId", data=options)
        return ShipStationStore().from_json(store)

    # TODO: return status code
    def deactivate_store(self, store_id):
        store_id = json.dumps({"storeId": str(store_id)})
        return self.post(endpoint="/stores/deactivate", data=store_id)

    def reactivate_store(self, store_id):
        store_id = json.dumps({"storeId": str(store_id)})
        store = self.post(endpoint="/stores/reactivate", data=store_id)
        return ShipStationStore().from_json(store)

    def list_users(self, show_inactive=False):
        self.require_type(show_inactive, bool)
        show_inactive = json.dumps({"showInactive": show_inactive})
        return self.object_list(
            self.get(endpoint="/users/", payload=show_inactive), ShipStationUser
        )

    def get_warehouse(self, warehouse_id):
        wh = self.get(endpoint="/warehouses/" + str(warehouse_id))
        return ShipStationWarehouse().from_json(wh)

    def list_warehouses(self):
        return self.object_list(self.get(endpoint="/warehouses"), ShipStationWarehouse)

    # TODO: return ShipStationWarehouse
    def create_warehouse(self, data):
        self.require_membership("origin_address", data)
        self.require_type(data.get("origin_address"), ShipStationAddress)
        data["origin_address"] = data["origin_address"].as_dict()
        if data["return_address"]:
            data["return_address"] = data["return_address"].as_dict()
        valid_options = json.dumps(
            self._validate_parameters(data, CREATE_WAREHOUSE_OPTIONS)
        )
        return self.post(endpoint="/warehouses/createwarehouse", data=valid_options)

    def delete_warehouse(self, warehouse_id):
        return self.delete(endpoint="/warehouses/" + str(warehouse_id))

    # TODO: return ShipStationWarehouse
    def update_warehouse(self, warehouse):
        self.require_type(warehouse, ShipStationWarehouse)
        wh = warehouse.json()
        return self.put(endpoint="/warehouses/" + str(warehouse.warehouse_id), data=wh)

    def list_webhooks(self):
        webhooks = self.get(endpoint="/webhooks").json()
        return [ShipStationWebhook().from_json(w) for w in webhooks.get('webhooks')]

    def unsubscribe_to_webhook(self, webhook_id):
        return self.delete(endpoint="/webhooks/" + str(webhook_id))

    def subscribe_to_webhook(self, options):
        # do not convert to camel case
        self.require_membership("target_url", SUBSCRIBE_TO_WEBHOOK_OPTIONS)
        self.require_membership("event", SUBSCRIBE_TO_WEBHOOK_OPTIONS)
        self.require_membership(
            options.get("event"), SUBSCRIBE_TO_WEBHOOK_EVENT_OPTIONS
        )
        return self.post(endpoint="/webhooks/subscribe", data=json.dumps(options))
