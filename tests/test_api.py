import pytest
from shipstation.models import *
from shipstation.api import ShipStation


secret_key, secret_secret = "8077d452600c4a64badc3b1aa6a0653f", "db0f8a3f0cc2481a9e9b12886b2cd395"
ss = ShipStation(secret_key, secret_secret)  #, debug=True)
carrier_code = ""


def test_webooks():
    subscribe_to_webhook_options = {"target_url": "http://someexamplewebhookurl.com/neworder", "event": "ORDER_NOTIFY","friendly_name": "pyshipstation test"}
    subscribed_to_webhook = ss.subscribe_to_webhook(subscribe_to_webhook_options)
    assert subscribed_to_webhook.status_code == 201
    webhook_id = subscribed_to_webhook.json()['id']
    _list_webhooks_(webhook_id, found=True)
    ss.unsubscribe_to_webhook(webhook_id)
    _list_webhooks_(webhook_id, found=False)


def _list_webhooks_(webhook_id=None, found=True):
    webhook_list = ss.list_webhooks()
    if found is False:
        with pytest.raises('KeyError'):
            webhook_list.json()['webhooks']
    webhooks_list = webhook_list.json()['webhooks']
    for webhook in webhooks_list:
        if webhook['WebHookID'] == webhook_id:
            assert webhook['WebHookID'] == webhook_id
    else:
        with pytest.raises('KeyError'):
            webhook['WebHookID']


def test_stores():
    marketplaces = ss.list_marketplaces()
    assert marketplaces.status_code == 200
    stores = ss.list_stores().json()
    assert len(stores) >= 1
    store_id = stores[-1].get('storeId')
    specific_store = ss.get_store(store_id)
    assert specific_store.status_code == 200
    r = ss.deactivate_store(store_id)
    assert r.status_code == 200
    r = ss.reactivate_store(store_id)
    assert r.status_code == 200


def test_warehouses():
    warehouses = ss.list_warehouses()
    assert warehouses.status_code == 200
    warehouses_id = warehouses.json()[0].get('warehouseId')
    warehouse = ss.get_warehouse(warehouse_id)
    assert warehouse.status_code == 200
    # ss.create_warehouse()
    # ss.update_warehouse()
    # ss.delete_warehouse()


def test_users():
    r = ss.list_users()
    assert r.status_code == 200


def test_carriers():
    r = ss.list_carriers()
    assert r.status_code == 200
    carrier_code = r.json()[0].get('code')
    r = ss.get_carrier(carrier_code)
    assert r.status_code == 200
    r = ss.list_packages(carrier_code)
    assert r.status_code == 200
    r = ss.list_services(carrier_code)
    assert r.status_code == 200


def test_customers():
    r = ss.list_customers()
    assert r.status_code == 200


def test_shipments_and_fulfillments():
    r = ss.get_rates(carrier_code)
    assert r.status_code == 200


def test_label_creation():
    pass
