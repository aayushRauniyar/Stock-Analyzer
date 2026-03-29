import os
from pathlib import Path
from dotenv import load_dotenv
import traceback

# Load backend/.env
load_dotenv(Path(__file__).parent / '.env')

print('APCA_API_KEY_ID present:', bool(os.getenv('APCA_API_KEY_ID')))
print('APCA_API_SECRET_KEY present:', bool(os.getenv('APCA_API_SECRET_KEY')))
print('APCA_API_BASE_URL:', os.getenv('APCA_API_BASE_URL'))

try:
    import alpaca_trade_api as tradeapi
    api = tradeapi.REST(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), os.getenv('APCA_API_BASE_URL'))
    account = api.get_account()
    print('Account status:', getattr(account, 'status', str(account)))
    print('Account equity:', getattr(account, 'equity', None))
    print('Account cash:', getattr(account, 'cash', None))
except Exception as e:
    print('Exception during Alpaca call:')
    traceback.print_exc()