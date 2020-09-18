#!/usr/bin/python

import sys
import os
import string
import json
import urllib
import datetime
import xml.etree.ElementTree as ET
import pdb
import ssl
import paho.mqtt.client as mqtt
import time


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

minNetatmoServerConnect = 150;

####################################################################################################
## MQTT constants
####################################################################################################
MQTT_SERVER = "localhost"
client = mqtt.Client()


####################################################################################################
## Netatmo constants
####################################################################################################

URL_RequestToken = 'https://api.netatmo.com/oauth2/token'
                 ## https://api.netatmo.com/oauth2/token
URL_DeviceList = 'http://api.netatmo.com/api/devicelist'
URL_GetMeasure = 'http://api.netatmo.com/api/getmeasure'
URL_GetStationData = 'https://api.netatmo.com/api/getstationsdata'
                ##https://api.netatmo.com/api/getstationsdata

PARM_Grant_Type = 'grant_type'
PARM_Grant_Type_Password = 'password'
PARM_Grant_Type_RefreshToken = 'refresh_token'
PARM_Client_Id = 'client_id'
PARM_Client_Secret = 'client_secret'  
PARM_Username = 'username'
PARM_Password = 'password'
PARM_Refresh_Token = 'refresh_token'

PARM_Access_Token = 'access_token'
PARM_Device_Id = 'device_id'
PARM_Module_Id = 'module_id'
PARM_Scale = 'scale'
PARM_Scale_Max = 'max'
PARM_Scale_30Min = '30min'
PARM_Scale_1Hour = '1hour'
PARM_Scale_3Hours = '3hours'
PARM_Scale_1Day = '1day'
PARM_Scale_1Week = '1week'
PARM_Scale_1Month = '1month'

PARM_Measure_Type = 'type'
PARM_Date_Begin = 'date_begin'
PARM_Date_End = 'date_end'
PARM_Date_End_Last = 'last'
PARM_Limit = 'limit'
PARM_Optimize = 'optimize'
PARM_Real_Time = 'real_time'

DATATYPE_Temperature = 'Temperature'
DATATYPE_Humidity = 'Humidity'
DATATYPE_CO2 = 'Co2'
DATATYPE_Pressure = 'Pressure'
DATATYPE_Noise = 'Noise'

RESPONSE_Status = 'status'
RESPONSE_Status_OK = 'ok'
RESPONSE_Body = 'body'


####################################################################################################
## DomoticZ constants
####################################################################################################

URL_JSON = "/json.htm"
PARM_Type = "type"
PARM_Type_Command = "command"
PARM_Param = "param"
PARM_Param_UpdateDevice = "udevice"
PARM_HardwareId = "hid"
PARM_DeviceId = "did"
PARM_DeviceUnit = "dunit"
PARM_DeviceType = "dtype"
PARM_DeviceSubType = "dsubtype"
PARM_NValue = "nvalue"
PARM_SValue = "svalue"

# status types for humidity
HUMSTAT_NORMAL = 0x0;
HUMSTAT_COMFORT = 0x1;
HUMSTAT_DRY = 0x2;
HUMSTAT_WET = 0x3;


####################################################################################################
## XML constants
####################################################################################################

TOKEN_ROOT = 'token'
TOKEN_ATTR_ACCESS_TOKEN = 'access_token'
TOKEN_ATTR_EXPIRES_IN = 'expires_in' 
TOKEN_ATTR_REFRESH_TOKEN = 'refresh_token'
TOKEN_ATTR_EXPIRED_AT = 'expired_at'

MEASURE_ROOT = 'measures'
MEASURE_outTemperature = 'out_temperature'
MEASURE_outHumidity = 'outHumidity'
##MEASURE_outTemp_trend = 'outTemp_trend'
MEASURE_outtime_utc = 'outtime_utc'
MEASURE_inTemperature = 'inTemperature'
MEASURE_inNoise =  'inNoise'
MEASURE_intime_utc = 'intime_utc' 
MEASURE_inpressure_trend =  'inpressure_trend'
MEASURE_inHumidity = 'inHumidity'
MEASURE_inPressure = 'inPressure'
MEASURE_inCO2 = 'inCO2'
MEASURE_inAbsolutePressure = 'inAbsolutePressure'
MEASURE_intime_utc_str= 'intime_utc_str'
MEASURE_outtime_utc_str = 'outtime_utc_str'
MEASURE_outMinTemp = 'outMinTemp'
MEASURE_outMaxTemp = 'outMaxTemp'


SETTINGS_ROOT = 'settings'
NODE_AUTHENTICATE = 'authentication'
ATTR_AUTH_CLIENT_ID = 'client_id'
ATTR_AUTH_CLIENT_SECRET= 'client_secret'
ATTR_AUTH_USERNAME = 'username'
ATTR_AUTH_PASSWORD = 'password'

NODE_DOMOTICZ = 'domoticz'
ATTR_DOMOTICZ_URL = 'url'
ATTR_DOMOTICZ_HARDWARE_ID = 'hardware_id'

DEVICES_ROOT = 'devices'
DEVICES_NODE_DEVICE = 'device'
DEVICES_NODE_MODULE = 'module' 
DEVICES_ID = 'id'
DEVICES_NODE_MEASURE = 'measure' 


####################################################################################################
## MQTT functiona
####################################################################################################

def on_connect(client, userdata, flags, rc):
    print("MQTT Connected with result code "+str(rc))

client.on_connect = on_connect

def SendMeasuresMQTT(measures):
    Log('SendMeasuresMQTT girdi')
    client.connect(MQTT_SERVER, 1883, 60)
    client.loop_start()
    client.publish("netatmo/outTemperature", measures.get(MEASURE_outTemperature))
    client.publish("netatmo/outHumidity", measures.get(MEASURE_outHumidity))
    ##client.publish("netatmo/outTemp_trend", measures.get(MEASURE_outTemp_trend))
    client.publish("netatmo/outtime_utc", measures.get(MEASURE_outtime_utc))
    client.publish("netatmo/inTemperature", measures.get(MEASURE_inTemperature))
   ## client.publish("netatmo/inNoise", measures.get(MEASURE_inNoise))
    client.publish("netatmo/intime_utc", measures.get(MEASURE_intime_utc))
    #client.publish("netatmo/inpressure_trend", measures.get(MEASURE_inpressure_trend))
    client.publish("netatmo/inHumidity", measures.get(MEASURE_inHumidity))
    client.publish("netatmo/inPressure", measures.get(MEASURE_inPressure))
    client.publish("netatmo/inCO2", measures.get(MEASURE_inCO2))
    ##client.publish("netatmo/inAbsolutePressure", measures.get(MEASURE_inAbsolutePressure))
    client.publish("netatmo/intime_utc_str" , measures.get(MEASURE_intime_utc_str))
    client.publish("netatmo/outtime_utc_str", measures.get(MEASURE_outtime_utc_str))
    client.publish("netatmo/outMinTemp", measures.get(MEASURE_outMinTemp))
    client.publish("netatmo/outMaxTemp", measures.get(MEASURE_outMaxTemp))
    

    time.sleep(4) # wait
    client.loop_stop()
    client.disconnect()
    pass    
 
    
####################################################################################################
## General functiona
####################################################################################################

def Log(message):
    sys.stderr.write("{}\n".format(message))
    

def GetWorkingPath():
    return os.path.dirname(os.path.realpath(__file__)) + os.sep


####################################################################################################
## Access token handling
####################################################################################################
    
def GetTokenFileName():
    return GetWorkingPath() + "token.xml"

def GetMeasuresFileName():
    return GetWorkingPath() + "measures.xml"

    
def SaveToken(token):
    Log('SaveToken girdi')
    token_filename = GetTokenFileName()
    if ET.iselement(token):
        try:
            ET.ElementTree(token).write(token_filename)
        except Exception:
            Log('ERROR: in SaveToken(%s)' % token_filename)            
            pass
    pass


    

def DeleteTokenFile():
    Log('DeleteTokenFile girdi')
    token_filename = GetTokenFileName()
    if os.path.isfile(token_filename):
        try:
            os.remove(token_filename)
        except:            
            Log('ERROR: in DeleteTokeFile(%s)' % token_filename)
            pass
    pass


def CreateToken(json_data):
    Log('CreateToken girdi')
    newtoken = ET.Element(TOKEN_ROOT)
    if newtoken != None and json_data != None:
        json_decoded = json.loads(json_data)
        newtoken.set(TOKEN_ATTR_ACCESS_TOKEN, json_decoded[TOKEN_ATTR_ACCESS_TOKEN])
        newtoken.set(TOKEN_ATTR_EXPIRES_IN, str(json_decoded[TOKEN_ATTR_EXPIRES_IN]))
        newtoken.set(TOKEN_ATTR_REFRESH_TOKEN, json_decoded[TOKEN_ATTR_REFRESH_TOKEN])
        expired_at = datetime.datetime.now() + datetime.timedelta(seconds = json_decoded[TOKEN_ATTR_EXPIRES_IN])
        newtoken.set(TOKEN_ATTR_EXPIRED_AT, expired_at.strftime("%Y-%m-%d %H:%M:%S"))
        SaveToken(newtoken)
    return newtoken




def GetAuthentication():
    Log('GetAuthentication girdi')
    authentication = {PARM_Client_Id: '', PARM_Client_Secret: '', PARM_Username: '', PARM_Password: ''}
    settings = LoadSettings()
    Log('LoadSettings cikti')
    if settings != None:
        authenticate = settings.find('.//%s' % NODE_AUTHENTICATE)
        if authenticate != None:
            if len(authenticate.get(ATTR_AUTH_CLIENT_ID)) > 0:
                authentication[PARM_Client_Id] = authenticate.get(ATTR_AUTH_CLIENT_ID)
                Log('ATTR_AUTH_CLIENT_ID(%s)' % authenticate.get(ATTR_AUTH_CLIENT_ID))
            if len(authenticate.get(ATTR_AUTH_CLIENT_SECRET)) > 0:
                authentication[PARM_Client_Secret] = authenticate.get(ATTR_AUTH_CLIENT_SECRET)
                Log('ATTR_AUTH_CLIENT_SECRET(%s)' % authenticate.get(ATTR_AUTH_CLIENT_SECRET))
            if len(authenticate.get(ATTR_AUTH_USERNAME)) > 0:
                authentication[PARM_Username] = authenticate.get(ATTR_AUTH_USERNAME)
                Log('ATTR_AUTH_USERNAME(%s)' % authenticate.get(ATTR_AUTH_USERNAME))
            if len(authenticate.get(ATTR_AUTH_PASSWORD)) > 0:
                authentication[PARM_Password] = authenticate.get(ATTR_AUTH_PASSWORD)
                Log('ATTR_AUTH_PASSWORD(%s)' % authenticate.get(ATTR_AUTH_PASSWORD))
            pass
        pass
    return authentication

def RequestToken():
    Log('RequestToken girdi')
    authentication = GetAuthentication()
    params = urllib.urlencode({
        PARM_Grant_Type: PARM_Grant_Type_Password,
        PARM_Client_Id: authentication[PARM_Client_Id],        
        PARM_Client_Secret: authentication[PARM_Client_Secret],
        PARM_Username: authentication[PARM_Username],
        PARM_Password: authentication[PARM_Password]
        })
    Log('params(%s)' % params)
    Log('URL_RequestToken(%s)' % URL_RequestToken)
    json_data = urllib.urlopen(URL_RequestToken, params, context=ctx).read()
    return CreateToken(json_data)


def RefreshToken(refresh_token):
    Log('RefreshToken girdi')
    authentication = GetAuthentication()
    params = urllib.urlencode({
        PARM_Grant_Type: PARM_Grant_Type_RefreshToken,
        PARM_Refresh_Token: refresh_token,
        PARM_Client_Id: authentication[PARM_Client_Id],        
        PARM_Client_Secret: authentication[PARM_Client_Secret]
        })
    json_data = urllib.urlopen(URL_RequestToken, params, context=ctx).read()
    return CreateToken(json_data)

    
def LoadToken():
    Log('LoadToken girdi')
    token_filename = GetTokenFileName()
    Log('LoadToken token_filename(%s)' % token_filename)
    if os.path.isfile(token_filename):
        try:
            tree = ET.parse(token_filename)
            root = tree.getroot()
            Log('LoadToken tree(%s)' % tree)
            Log('LoadToken root(%s)' % root)
            return root
        except:            
            Log('ERROR: in LoadToken(%s)' % token_filename)
            pass
    else:
         Log('dosya bulunamadi! (%s)' % token_filename)
    return RequestToken()


def GetToken():
    Log('GetToken girdi')
    token = LoadToken()
    if token != None:
        try:
            # we should always have a token
            expired_at = datetime.datetime.strptime(token.get(TOKEN_ATTR_EXPIRED_AT), "%Y-%m-%d %H:%M:%S")
            if expired_at < datetime.datetime.now() + datetime.timedelta(seconds = 30):
                # is expired or will expire within 30 seconds: Refresh the token
                token = RefreshToken(token.get(TOKEN_ATTR_REFRESH_TOKEN))
            pass
        except:
            token = None
            pass
    if token == None:
        DeleteTokenFile()
    return token                                 


def SaveMeasures(measures):
    Log('SaveMeasures girdi')
    measure_filename = GetMeasuresFileName()
    if ET.iselement(measures):
        try:
            ET.ElementTree(measures).write(measure_filename)
        except Exception:
            Log('ERROR: in SaveMeasures(%s)' % measure_filename)            
            pass
    pass



def CreateMeasures(mDashboard_data, inDashboard_data, intime_utc_str, outtime_utc_str):
    Log('CreateMeasures girdi')
    newMeasures = ET.Element('measures')
    if newMeasures != None:
        outTemperature = mDashboard_data['Temperature']
        outHumidity = mDashboard_data['Humidity']
        ##outTemp_trend = mDashboard_data['temp_trend']
        outtime_utc = mDashboard_data['time_utc']
        inTemperature = inDashboard_data['Temperature']
        inNoise = inDashboard_data['Noise']
        intime_utc = inDashboard_data['time_utc']
        #inpressure_trend= inDashboard_data['pressure_trend']
        inHumidity = inDashboard_data['Humidity']
        inPressure = inDashboard_data['Pressure']
        inCO2 = inDashboard_data['CO2']
        inAbsolutePressure = inDashboard_data['AbsolutePressure']
        outMinTemp = mDashboard_data['min_temp']
        outMaxTemp = mDashboard_data['max_temp']


        newMeasures.set(MEASURE_outTemperature, str(outTemperature))
        newMeasures.set(MEASURE_outHumidity, str(outHumidity))
        ##newMeasures.set(MEASURE_outTemp_trend, str(outTemp_trend))
        newMeasures.set(MEASURE_outtime_utc, str(outtime_utc))
        newMeasures.set(MEASURE_inTemperature, str(inTemperature))
        newMeasures.set(MEASURE_inNoise,  str(inNoise))
        newMeasures.set(MEASURE_intime_utc, str(intime_utc))
        #newMeasures.set(MEASURE_inpressure_trend,  inpressure_trend)
        newMeasures.set(MEASURE_inHumidity, str(inHumidity))
        newMeasures.set(MEASURE_inPressure, str(inPressure))
        newMeasures.set(MEASURE_inCO2, str(inCO2))
        newMeasures.set(MEASURE_inAbsolutePressure, str(inAbsolutePressure))
        newMeasures.set(MEASURE_intime_utc_str, intime_utc_str)
        newMeasures.set(MEASURE_outtime_utc_str, str(outtime_utc_str))
        newMeasures.set(MEASURE_outMinTemp, str(outMinTemp))
        newMeasures.set(MEASURE_outMaxTemp, str(outMaxTemp))
        
    return newMeasures

def LoadMeasures():
    Log('LoadMeasures girdi')
    measures_filename = GetMeasuresFileName()
    Log('LoadMeasures measures_filename(%s)' % measures_filename)
    if os.path.isfile(measures_filename):
        try:
            tree = ET.parse(measures_filename)
            root = tree.getroot()
            Log('LoadMeasures tree(%s)' % tree)
            Log('LoadMeasures root(%s)' % root)
            return root
        except:            
            Log('ERROR: in LoadMeasures(%s)' % measures_filename)
            pass
    else:
         Log('dosya bulunamadi! (%s)' % measures_filename)
    return None


def GetMeasuresForMQTT(token):
    Log('GetMeasuresForMQTT girdi')
    expired = False
    measures = LoadMeasures()
    if  measures != None:
        Log('measures (%s)' % measures)

            # we should always have a token
        modified_at = os.path.getmtime(GetMeasuresFileName())
        diff = time.time() - os.path.getmtime(GetMeasuresFileName())
        Log('diff (%s)' % diff)
           
        if diff > minNetatmoServerConnect :
                # is expired or will expire within 30 seconds: Refresh the token
            expired = True
            Log('expired')

    Log('measures (%s)' % measures)
    if measures == None or expired:
        Log('measures none or expired')
        measures = GetStationData(token)
        SaveMeasures(measures)
    SendMeasuresMQTT(measures)
    return None                

####################################################################################################
## Devices
####################################################################################################
    
def GetSettingsFileName():
    return GetWorkingPath() + "netatmo_settings.xml"


def AddSubElement(node, tag):
    Log('AddSubElement girdi')
    if node != None and tag != None:
        return ET.SubElement(node, tag)
    return None

    
def SaveSettings(settings):
    Log('SaveSettings girdi')
    filename = GetSettingsFileName()
    if ET.iselement(settings):
        try:
            ET.ElementTree(settings).write(filename)
        except Exception:
            Log('ERROR: in SaveSettings(%s)' % filename)            
            pass
    pass    
    

def CreateSettings():
    Log('CreateSettings girdi')
    settings = ET.Element(SETTINGS_ROOT)
    Log('SETTINGS_ROOT(%s)' % SETTINGS_ROOT)
    if settings != None:
        authenticate = AddSubElement(settings, NODE_AUTHENTICATE)
        authenticate.set(ATTR_AUTH_CLIENT_ID, 'CLIENT_ID')
        authenticate.set(ATTR_AUTH_CLIENT_SECRET, 'CLIENT_SECRET')
        authenticate.set(ATTR_AUTH_USERNAME, 'USERNAME')
        authenticate.set(ATTR_AUTH_PASSWORD, 'PASSWORD')
        domoticz = AddSubElement(settings, NODE_DOMOTICZ)
        domoticz.set(ATTR_DOMOTICZ_URL, 'http://127.0.0.1:8080')
        domoticz.set(ATTR_DOMOTICZ_HARDWARE_ID, '10')
        devices = AddSubElement(settings, DEVICES_ROOT)
        SaveSettings(settings)
    return settings


def LoadSettings():
    Log('LoadSettings girdi')
    filename = GetSettingsFileName()
    Log('GetSettingsFileName %s)' % filename)
    if os.path.isfile(filename):
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            return root
        except:            
            Log('ERROR: in LoadSettings(%s)' % filename)
            pass
    else:
        Log('dosya bulunamadi! (%s)' % filename)
    return CreateSettings()   
    

def GetDomoticzIds(device_ids, device_id, module_id, data_type):
    Log('GetDomoticzIds girdi')
    domoticz_ids = {"domoticz_dev_id" : "", "domoticz_dev_type": "", "domoticz_dev_subtype" : ""}
    if device_ids != None:
        try:
            device_present = False
            # cannot get this one to work (using multiple attributes)
            xpath = '//%s[@id="%s" and @module_id="%s" and @data_type="%s"]' % (DEVICES_NODE_DEVICE, device_id, module_id, data_type)
            xpath = './/%s[@id="%s"]' % (DEVICES_NODE_DEVICE, device_id)
            device_list = device_ids.findall(xpath)
            for device in device_list:
                if device.get("module_id") == module_id and device.get("data_type") == data_type:
                    device_present = True
                    domoticz_ids["domoticz_dev_id"] = device.get("domoticz_dev_id")
                    domoticz_ids["domoticz_dev_type"] = device.get("domoticz_dev_type")
                    domoticz_ids["domoticz_dev_subtype"] = device.get("domoticz_dev_subtype")
                    break
            if device_present == False:
                new_device = AddSubElement(device_ids, DEVICES_NODE_DEVICE)
                new_device.set("id", device_id)
                new_device.set("module_id", module_id)
                new_device.set("data_type", data_type)
                new_device.set("domoticz_dev_id", "")
                new_device.set("domoticz_dev_type", "")
                new_device.set("domoticz_dev_subtype", "")
        except:
            pass
    return domoticz_ids
                    
    
def AddMeasures(root, data_types, device_ids):
    Log('AddMeasures girdi')
    if root == None or data_types == None:
        return
    device_id = root.get(DEVICES_ID)
    module_id = root.get("module_id")
    for data_type in data_types:
        data_element = AddSubElement (root, DEVICES_NODE_MEASURE)         
        data_element.set("data_type", data_type)
        domoticz_ids = GetDomoticzIds(device_ids, device_id, module_id, data_type)
        for domoticz_id in domoticz_ids.keys():
            data_element.set(domoticz_id, domoticz_ids[domoticz_id])
    pass


def AddDevices(root, devices, device_ids, unit, is_module):
    Log('AddDevices girdi')
    if root == None or devices == None or device_ids == None:
        return unit
    for device in devices:
        unit += 1
        if is_module == True:
            device_id = device["main_device"]
            module_id = device["_id"]
        else:
            device_id = device["_id"]
            module_id = ""
        module_name = device["module_name"]
        device_element = AddSubElement (root, DEVICES_NODE_DEVICE)         
        device_element.set(DEVICES_ID, device_id); 
        device_element.set("module_id", module_id); 
        device_element.set("module_name", module_name);
        device_element.set("dunit", str(unit))
        AddMeasures(device_element, device["data_type"], device_ids)        
    return unit


def GetMeasures(devices, access_token):
    Log('GetMeasures girdi')
    try:
        # cannot get this one to work using multiple attributes
        xpath = './/%s' % DEVICES_NODE_DEVICE
        device_list = devices.findall(xpath)
        for device in device_list:
            device_id = device.get("id")
            module_id = device.get("module_id")
            xpath_measure = './/%s' % DEVICES_NODE_MEASURE
            measure_list = device.findall(xpath_measure)
            for measure in measure_list:
                if module_id != None:
                    params = urllib.urlencode({
                        PARM_Access_Token: access_token,
                        PARM_Device_Id: device_id,
                        PARM_Module_Id: module_id,
                        PARM_Scale: PARM_Scale_Max,
                        PARM_Measure_Type: measure.get("data_type"),
                        PARM_Date_End: PARM_Date_End_Last,
                        PARM_Optimize: "True"                    
                        })
                else:
                    params = urllib.urlencode({
                        PARM_Access_Token: access_token,
                        PARM_Device_Id: device_id,
                        PARM_Scale: PARM_Scale_Max,
                        PARM_Measure_Type: measure.get("data_type"),
                        PARM_Date_End: PARM_Date_End_Last,
                        PARM_Optimize: "True"                    
                        })
                json_data = urllib.urlopen(URL_GetMeasure, params,  context=ctx).read()
                measure_response = json.loads(json_data)
                if measure_response != None and RESPONSE_Status in measure_response.keys() and measure_response[RESPONSE_Status] == RESPONSE_Status_OK:
                    body = measure_response[RESPONSE_Body]
                    value = body[0]["value"][0][0]
                    measure.set("value", str(value))
                    pass
    except:
        pass    
    #pass


def MeasureIsValid(measure):
    Log('MeasureIsValid girdi')
    if measure.get("data_type") != None and len(measure.get("data_type")) > 0 and \
       measure.get("domoticz_dev_id") != None and len(measure.get("domoticz_dev_id")) > 0 and \
       measure.get("domoticz_dev_type") != None and len(measure.get("domoticz_dev_type")) > 0 and \
       measure.get("domoticz_dev_subtype") != None and len(measure.get("domoticz_dev_subtype")) > 0 and \
       measure.get("value") != None and len(measure.get("value")) > 0:
        return True
    return False


def AddQueryParameter(name, value, cat = '&'):
    return '%s%s=%s' % (cat, name, value)


def GetNSValues(data_type, value):
    Log('GetNSValues girdi')
    values = { PARM_NValue: "0", PARM_SValue: "0" }
    if data_type == DATATYPE_Temperature:
        values[PARM_SValue] = value
    elif data_type == DATATYPE_Humidity:
        values[PARM_NValue] = value
        intvalue =int(value)
        if intvalue < 40:
            values[PARM_SValue] = HUMSTAT_DRY
        elif intvalue > 90:
            values[PARM_SValue] = HUMSTAT_WET
        elif intvalue >= 50 and intvalue <= 70:
            values[PARM_SValue] = HUMSTAT_COMFORT
        else:
            values[PARM_SValue] = HUMSTAT_NORMAL                    
    elif data_type == DATATYPE_CO2:
        values[PARM_NValue] = value
    elif data_type == DATATYPE_Pressure:
        values[PARM_SValue] = value
    elif data_type == DATATYPE_Noise:
        values[PARM_NValue] = value
    return values


def TransferSingleMeasure(url, hardware_id, unit, measure):
    Log('TransferSingleMeasure girdi')
    if MeasureIsValid(measure):
        url = '%s%s' % (url, URL_JSON)
        url += AddQueryParameter(PARM_Type, PARM_Type_Command, '?')
        url += AddQueryParameter(PARM_Param, PARM_Param_UpdateDevice)
        url += AddQueryParameter(PARM_HardwareId, hardware_id)
        url += AddQueryParameter(PARM_DeviceId, measure.get("domoticz_dev_id"))
        url += AddQueryParameter(PARM_DeviceUnit, unit)
        url += AddQueryParameter(PARM_DeviceType, measure.get("domoticz_dev_type"))
        url += AddQueryParameter(PARM_DeviceSubType, measure.get("domoticz_dev_subtype"))
        values = GetNSValues(measure.get("data_type"), measure.get("value"))
        for value in values.keys():
            url += AddQueryParameter(value, values[value])
        urllib.urlopen(url, context=ctx)
        pass
    pass


def TransferMeasures(devices, url, hardware_id):
    Log('TransferMeasures girdi')
    # Transfer all measurements to DomoticZ
    try:
        xpath = './/%s' % DEVICES_NODE_DEVICE
        device_list = devices.findall(xpath)
        for device in device_list:
            unit = device.get("dunit")
            xpath_measure = './/%s[@value]' % DEVICES_NODE_MEASURE
            measure_list = device.findall(xpath_measure)
            for measure in measure_list:
                TransferSingleMeasure(url, hardware_id, unit, measure)
                pass
        pass
    except:
        Log("Error in TransferMeasures")
        pass    
    #ET.dump(devices)
    pass


def HandleDevices(json_data, access_token):
    Log('HandleDevices girdi')
    Log('json_data(%s)' % json_data)  
    if json_data != None:
        try:
            device = json.loads(json_data)
            if RESPONSE_Status in device.keys() and RESPONSE_Body in device.keys() and device[RESPONSE_Status] == RESPONSE_Status_OK:
                body = device[RESPONSE_Body]
                settings = LoadSettings()
                domoticz = settings.find('.//%s' % NODE_DOMOTICZ)                
                device_ids = settings.find('.//%s' % DEVICES_ROOT)
                devices = ET.Element(DEVICES_ROOT)
                if devices != None:
                    # Build the actual device list
                    unit = AddDevices(devices, body['devices'], device_ids, 0, False)
                    unit = AddDevices(devices, body['modules'], device_ids, unit, True)
                    if domoticz != None and domoticz.get(ATTR_DOMOTICZ_HARDWARE_ID) == None:
                        domoticz.set(ATTR_DOMOTICZ_HARDWARE_ID, "100")
                    SaveSettings(settings)
                    # Get the actual measurement values from Netatmo service
                    GetMeasures(devices, access_token)
                    if domoticz != None and domoticz.get(ATTR_DOMOTICZ_URL) != None:
                        # Transfer the measurements to DomoticZ
                        TransferMeasures(devices, domoticz.get(ATTR_DOMOTICZ_URL), domoticz.get(ATTR_DOMOTICZ_HARDWARE_ID))
        except:
            pass
    pass

    
def UpdateDeviceList(access_token):
    Log('UpdateDeviceList girdi')
    Log('access_token(%s)' % access_token)  
    if access_token != None:
        params = urllib.urlencode({
            PARM_Access_Token: access_token
            })
        Log('params(%s)' % params)
        json_data = urllib.urlopen(URL_DeviceList, params, context=ctx).read()
        HandleDevices(json_data, access_token)
    pass



def GetStationData(access_token):
    Log('GetStationData girdi')
    Log('access_token(%s)' % access_token)  
    if access_token != None:
        params = urllib.urlencode({
            PARM_Access_Token: access_token
            })
        Log('params(%s)' % params)
        json_data = urllib.urlopen(URL_GetStationData, params, context=ctx).read()
        ##Log('json_data(%s)' % json_data)
        if json_data != None:
                    allJsonData = json.loads(json_data)
                    rawData = allJsonData['body']['devices']
                    if not rawData : raise NoDevice("No weather station available")
                    stations = { d['_id'] : d for d in rawData }
                    modules = dict()
                    module = rawData[0]['modules'][0]
                    print(module)
                    mDashboard_data = module['dashboard_data']
                    inDashboard_data = rawData[0]['dashboard_data']
                    
                    outTemperature = mDashboard_data['Temperature']
                    outHumidity = mDashboard_data['Humidity']
                   ## outTemp_trend = mDashboard_data['temp_trend']
                    outtime_utc = mDashboard_data['time_utc']
                    outMinTemp = mDashboard_data['min_temp']
                    outMaxTemp = mDashboard_data['max_temp'] 

                    inTemperature = inDashboard_data['Temperature']
                    inNoise = inDashboard_data['Noise']
                    intime_utc = inDashboard_data['time_utc']
                    #inpressure_trend= inDashboard_data['pressure_trend']
                    inHumidity = inDashboard_data['Humidity']
                    inPressure = inDashboard_data['Pressure']
                    inCO2 = inDashboard_data['CO2']
                    inAbsolutePressure = inDashboard_data['AbsolutePressure']

                    from datetime import datetime
                    intime_utc_str = datetime.fromtimestamp(int(intime_utc)).strftime('%Y-%m-%d_%H:%M:%S')
                    outtime_utc_str = datetime.fromtimestamp(int(outtime_utc)).strftime('%Y-%m-%d_%H:%M:%S')
                    import time
                    tsNow = time.time()
                    difOutTime = tsNow - int(outtime_utc);
                    difInTime = tsNow - int(intime_utc);
                    
                    Log('*')
                    Log('mDashboard_data(%s)' % mDashboard_data)
                    Log('tsNow(%s)' % tsNow)
                    Log('difOutTime(%s)' % difOutTime)
                    Log('difInTime(%s)' % difInTime)
                    Log('intime_utc_str(%s)' % intime_utc_str)
                    Log('outtime_utc_str(%s)' % outtime_utc_str)
                    Log('outHumidity(%s)' % outHumidity)
                    Log('outTemperature(%s)' % outTemperature)
                    ##Log('outTemp_trend(%s)' % outTemp_trend)

                    Log('inTemperature(%s)' % inTemperature)
                    Log('inNoise(%s)' % inNoise)
                    Log('intime_utc(%s)' % intime_utc)
                    #Log('inpressure_trend(%s)' % inpressure_trend)                              
                    Log('inHumidity(%s)' % inHumidity)
                    Log('inPressure(%s)' % inPressure)  
                    Log('inCO2(%s)' % inCO2)
                    Log('inAbsolutePressure(%s)' % inAbsolutePressure)
                    Log('outMinTemp(%s)' % outMinTemp)
                    Log('outMaxTemp(%s)' % outMaxTemp)

                    if (difOutTime > 3000):
                        outtime_utc_str = 'outofdate'
                    if (difInTime > 3000):
                        intime_utc_str = 'outofdate'
                    measures = CreateMeasures(mDashboard_data, inDashboard_data, intime_utc_str, outtime_utc_str)
                    return measures
                    pass
    pass

####################################################################################################
## Main entry
####################################################################################################

def main():
    ###pdb.set_trace()
    token = GetToken()
    
    if token != None:
        measures = GetMeasuresForMQTT(token.get(TOKEN_ATTR_ACCESS_TOKEN))
       ## GetStationData(token.get(TOKEN_ATTR_ACCESS_TOKEN))
        
    
if __name__ == "__main__":
    main()



