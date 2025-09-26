# core
import argparse
import asyncio
import copy
import requests

# community
#from pynut3 import nut3
import PyNUTClient.PyNUT
import yaml

CHARGE_STATES = {
  'OL': 5,
  'OL CHRG': 4,
  'OB DISCHRG': 3,
  'LB': 2,
  'RB': 1
}

def stateToInt(state):
  if state in CHARGE_STATES:
    return CHARGE_STATES[state]
  return -1

async def fetch_metrics():
  config = yaml.safe_load(open('conf/ups-metric-sender.yaml'))
  UrlMetricPacker = f"{config['api']['protocol']}://{config['api']['host']}:{config['api']['port']}/api/metrics"

  while True:
    print (f'- Retrieving UPS metrics for {args.ups}')
    StringDict = getUpsDataAsStringDict(ups, args.ups)
    metrics = {
      "charge.percent": int(StringDict['battery.charge']),
      'charge.state.value': stateToInt(StringDict['ups.status']),
      'charge.state.raw': StringDict['ups.status'],
      'load.percent': int(StringDict['ups.load']),
      'runtime.second': int(StringDict['battery.runtime']),
    }
    print (metrics)

    # prepare a version of metrics without some fields
    StrippedMetrics = copy.deepcopy(metrics)
    del StrippedMetrics['charge.state.raw']

    # POST to API endpoint
    payload = {
      'DeviceId': 'myups',
      'metrics': StrippedMetrics
    }
    try:
      resp = requests.post(UrlMetricPacker, json=payload)
      print (f'- Posted to {UrlMetricPacker}, response code: {resp.status_code}')
    except Exception as e:
      print (f'Error posting to {UrlMetricPacker}: {e}')

    # Wait for 10 seconds before the next request
    await asyncio.sleep(10)


def getUpsDataAsStringDict(UpsClient, UpsName):
  ByteDict = UpsClient.GetUPSVars(ups=UpsName)
  StringDict = {key.decode(): value.decode() for key, value in ByteDict.items()}
  return StringDict

def validateUpsName(UpsClient, UpsName):
  UpsNames = UpsClient.GetUPSNames()
  if not UpsName in UpsNames:
    print (f'Invalid UPS name: {UpsName}')
    print (f'Valid names are: {UpsNames}')
    exit(1)

def dumpAllMetrics(UpsClient, UpsName):
  StringDict = getUpsDataAsStringDict(UpsClient, UpsName)
  for key in StringDict:
    print (f'{key}: {StringDict[key]}')
  exit(0)

def dumpProductInfo(UpsClient, UpsName):
  StringDict = getUpsDataAsStringDict(UpsClient, UpsName)
  print (f'UPS Vendor: {StringDict["ups.mfr"]}')
  print (f'UPS Model: {StringDict["ups.model"]}')
  print (f'UPS Product ID: {StringDict["ups.productid"]}')
  print (f'UPS Serial: {StringDict["ups.serial"]}')
  print (f'UPS Status: {StringDict["ups.vendorid"]}')
  exit(0)

# Set up argument parser
parser = argparse.ArgumentParser(description="UPS Metric Sender")
parser.add_argument('-i', "--info", 
  action="store_true", 
  help="Dump UPS info")
parser.add_argument('-d', "--dump", 
  action="store_true", 
  help="Dump all metrics")
parser.add_argument('-u', "--ups", 
  type=str, 
  default='myups', 
  help="Name of the UPS to fetch metrics from (default: myups)")
args = parser.parse_args()

ups = PyNUTClient.PyNUT.PyNUTClient()

if args.dump:
  print (f'- Dumping all metrics for {args.ups}')
  ups = PyNUTClient.PyNUT.PyNUTClient()
  validateUpsName(ups, args.ups)
  dumpAllMetrics(ups, args.ups)
elif args.info:
  print (f'- Dumping UPS info for {args.ups}')
  ups = PyNUTClient.PyNUT.PyNUTClient()
  validateUpsName(ups, args.ups)
  dumpProductInfo(ups, args.ups)

#print(dir(PyNUTClient))
# ensure ups name is valid
validateUpsName(ups, args.ups)

# Run the async loop
asyncio.run(fetch_metrics())
