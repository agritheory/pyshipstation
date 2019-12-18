import pytest
from shipstation.models import *
from shipstation.aio import ShipStation


secret_key, secret_secret = "8077d452600c4a64badc3b1aa6a0653f", "db0f8a3f0cc2481a9e9b12886b2cd395"
ss = ShipStation(secret_key, secret_secret, debug=True, timeout=5)


async def test_carriers():
    r = await ss.list_carriers()
    carrier_code = r.json()[0].get('code')
    r = await ss.get_carrier(carrier_code)
    r = await ss.list_packages(carrier_code)
    r = await ss.list_services(carrier_code)
