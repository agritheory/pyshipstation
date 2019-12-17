import datetime
from decimal import Decimal
import json
import pprint
import requests
from shipstation.models import *
from shipstation.constants import *


class ShipStation(ShipStationBase):
    """
    Handles the details of connecting to and querying a ShipStation account.
    """

    def __init__(self, key=None, secret=None, debug=False):
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
        self.timeout = 1.0
        self.debug = debug

    def add_order(self, order):
        self.require_type(order, ShipStationOrder)
        self.orders.append(order)

    def get_orders(self):
        return self.orders

    def submit_orders(self):
        for order in self.orders:
            self.post(endpoint="/orders/createorder", data=json.dumps(order.as_dict()))

    def get(self, endpoint="", payload=None):
        url = "{}{}".format(self.url, endpoint)
        r = requests.get(
            url, auth=(self.key, self.secret), params=payload, timeout=self.timeout
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint('GET ' + url)
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
            timeout=self.timeout
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
            pprint.PrettyPrinter(indent=4).pprint('PUT ' + url)
            pprint.PrettyPrinter(indent=4).pprint(r.json())

        return r

    def delete(self, endpoint="", payload=None):
        url = "{}{}".format(self.url, endpoint)
        r = requests.delete(
            url,
            auth=(self.key, self.secret),
            params=payload,
            timeout=self.timeout
        )
        if self.debug:
            pprint.PrettyPrinter(indent=4).pprint('DELETE ' + url)
            pprint.PrettyPrinter(indent=4).pprint(r)

        return r

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

    def list_carriers(self):
        return self.get(endpoint="/carriers/")

    def get_carrier(self, carrier_code):
        return self.get(
            endpoint="/carriers/getcarrier", payload={"carrierCode": carrier_code}
        )

    def list_packages(self, carrier_code):
        return self.get(
            endpoint="/carriers/listpackages", payload={"carrierCode": carrier_code}
        )

    def list_services(self, carrier_code):
        return self.get(
            endpoint="/carriers/listservices", payload={"carrierCode": carrier_code}
        )

    def get_customer(self, customer_id):
        return self.get(
            endpoint="/customers/customerId", payload={"carrierCode": customer_id}
        )

    def list_customers(self, parameters={}):
        valid_parameters = self._validate_parameters(
            parameters, CUSTOMER_LIST_PARAMETERS
        )
        return self.get(endpoint="/customers", payload=valid_parameters)

    def list_fulfillments(self, parameters={}):
        valid_parameters = self._validate_parameters(
            parameters, FULFILLMENT_LIST_PARAMETERS
        )
        return self.get(endpoint="/fulfillments", payload=valid_parameters)

    def list_shipments(self, parameters={}):
        valid_parameters = self._validate_parameters(
            parameters, SHIPMENT_LIST_PARAMETERS
        )
        return self.get(endpoint="/shipments", payload=valid_parameters)

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

    def void_label(self, shipment_id):
        return self.post(endpoint="/shipments/voidlabel", data=shipment_id)

    def list_stores(self, show_inactive=False, marketplace_id=None):
        self.require_type(show_inactive, bool)
        self.require_type(marketplace_id, int)
        parameters = {}
        if show_inactive:
            parameters['showInactive'] = show_inactive
        if marketplace_id:
            parameters['marketplaceId'] = marketplace_id
        return self.get(endpoint="/stores", payload=parameters)

    def get_store(self, store_id):
        return self.get(endpoint="/stores/" + str(store_id))

    def update_store(self, options):
        options = self._validate_parameters(options, UPDATE_STORE_OPTIONS)
        [self.require_attribute(m) for m in UPDATE_STORE_OPTIONS]
        self.require_type(options.get("status_mappings"), list)
        for mapping in status_mappings:
            self.require_type(mapping, ShipStationStatusMapping)
            self.require_membership(mapping["orderStatus"], ORDER_STATUS_VALUES)
        self.put(endpoint="/stores/storeId", data=options)

    def list_marketplaces(self):
        return self.get(endpoint="/stores/marketplaces/")

    def deactivate_store(self, store_id):
        store_id = json.dumps({"storeId": str(store_id)})
        return self.post(endpoint="/stores/deactivate", data=store_id)

    def reactivate_store(self, store_id):
        store_id = json.dumps({"storeId": str(store_id)})
        return self.post(endpoint="/stores/reactivate", data=store_id)

    def list_users(self, show_inactive=False):
        self.require_type(show_inactive, bool)
        show_inactive = json.dumps({"showInactive": show_inactive})
        return self.get(endpoint="/users/", payload=show_inactive)

    def get_warehouse(self, warehouse_id):
        return self.get(endpoint="/warehouses/" + str(warehouse_id))

    def list_warehouses(self):
        return self.get(endpoint="/warehouses")

    def delete_warehouse(self, warehouse_id):
        return self.delete(endpoint="/warehouses/" + str(warehouse_id))

    def update_warehouse(self, warehouse_id, options):
        options = self._validate_parameters(options, UPDATE_WAREHOUSE_OPTIONS)
        [self.require_attribute(m) for m in UPDATE_WAREHOUSE_OPTIONS]
        self.require_type(options.get("origin_address"), ShipStationAddress)
        self.require_type(options.get("return_address"), ShipStationAddress)
        self.require_type(options.get("create_date"), datetime.datetime)
        self.require_type(options.get("return_address"), Boolean)
        self.put(endpoint="/stores/storeId", data=options)

    def list_webhooks(self):
        return self.get(endpoint="/webhooks")

    def unsubscribe_to_webhook(self, webhook_id):
        return self.delete(endpoint="/webhooks/" + str(webhook_id))

    def subscribe_to_webhook(self, options):
        # do not convert to camel case
        self.require_membership("target_url", SUBSCRIBE_TO_WEBHOOK_OPTIONS)
        self.require_membership("event", SUBSCRIBE_TO_WEBHOOK_OPTIONS)
        self.require_membership(options.get("event"), SUBSCRIBE_TO_WEBHOOK_EVENT_OPTIONS)
        return self.post(endpoint="/webhooks/subscribe", data=json.dumps(options))
