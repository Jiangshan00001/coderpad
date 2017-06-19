import asyncio
import datetime
import random
import websockets
import sys
import concurrent
import json

#http://websockets.readthedocs.io/en/stable/intro.html
g_text=''


"""
{
padname1:{'ws':{ws1:{}, ws2:{}}, 'data':{'dict':data_dict}  }
padname2:{}
}
"""


g_pads={
    #'demo1':{'ws': [], 'data': {'dict':{}}   },
    "pads":{},
    #ws1:{'pad_name_list':[''],'address':addr_str, 'sec_token':'ttttt' }
    "ws":{    }
}

def create_pad(pad_name):
    global g_pads
    if pad_name not in g_pads['pads']:
        g_pads['pads'][pad_name] = {'ws': [], 'data': {'dict':{}}}
        return 'ok'
    return 'error-already_exist'

def delete_pad(pad_name):
    global g_pads
    if pad_name in g_pads['pads']:
        del g_pads['pads'][pad_name]
        return 'ok'
    else:
        return 'error-not exist'

def add_ws(ws):
    global g_pads
    if ws not in g_pads['ws']:
        print('ws added. %s', ws)
        g_pads['ws'][ws]={'pads':[]}
        print('ws size=', len(g_pads['ws']))
    else:
        print('ws already in. add failure.', ws)

def go_to_pad(ws, pad_name):
    global g_pads
    if ws not in g_pads['ws']:
        raise 'go to pad error. ws not exist'

    if pad_name in g_pads['ws'][ws]['pads']:
        return 'error-already in pad'
    g_pads['ws'][ws]['pads'].append(pad_name)
    g_pads['pads'][pad_name]['ws'].append(ws)
    return 'ok'

def remove_ws(ws):
    global g_pads
    if ws not in g_pads['ws']:
        raise 'remove_ws error. ws not exist'

    for pname in g_pads['ws'][ws]['pads']:
        g_pads['pads'][pname]['ws'].remove(ws)

    del g_pads['ws'][ws]
    print('remove ok. ws size=', len(g_pads['ws']))
    return 'ok'


def setdata(pad_name, data):
    global g_pads
    g_pads['pads'][pad_name]['data']['dict']=data

def getdata(pad_name):
    global g_pads
    return g_pads['pads'][pad_name]['data']['dict']

def replacedata(pad_name, data):
    global g_pads
    return g_pads['pads'][pad_name]['data']['dict'].update(data)




"""
cmd:
listpads


create padname
delete padname
goto padname

getprotocollist 无参数
start padname
stop padname
getStatus padname

setDispType typename
getDispType 

set padname data
getLen
getAll
get pos len
insert pos data
remove pos len
replace pos newData

login
logout

chart

plugin
serverbase
"""


g_ts=0

#==========================
async def consumer(ws, msg):
    """
    对于接收到的命令，进行处理
    :param ws: 
    :param msg: 
    :return: 
    """

    global g_pads,g_ts

    g_ts=g_ts+1
    msg=json.loads(msg)



    if 'cmd' in msg:
        print('processing cmd',msg['cmd'])
        if msg['cmd']=='listpads':
            await ws.send(json.dumps({'status': 'ok', 'ts': g_ts,'cmd':msg['cmd'],  'pads':list(g_pads['pads'].keys())}))
        elif msg['cmd']=='create':
            status=create_pad(msg['pad_name'])
            await ws.send(json.dumps({'cmd':msg['cmd'],'status':status,'ts':g_ts}))
        elif msg['cmd']=='delete':
            status = delete_pad(msg['pad_name'])
            await ws.send(json.dumps({'cmd':msg['cmd'],'status':status,'ts':g_ts, 'pad_name':msg['pad_name']}))
        elif msg['cmd']=='goto':
            status = go_to_pad(ws, msg['pad_name'])
            await ws.send(json.dumps({'cmd':msg['cmd'],'status':status,'ts':g_ts,'pad_name':msg['pad_name']}))
        elif msg['cmd']=='set':
            if msg['pad_name'] not in g_pads['pads']:
                await ws.send(json.dumps({'cmd': msg['cmd'], 'status': 'error', 'error_msg':'pad name does not exist', 'ts': g_ts}))
                return
            setdata(msg['pad_name'], msg['data'])
            print('got set data:',msg['data'])
            await ws.send(json.dumps({'cmd':msg['cmd'],'status':'ok','ts':g_ts}))
        elif msg['cmd']=='getLen':
            if msg['pad_name'] not in g_pads['pads']:
                await ws.send(json.dumps({'cmd': msg['cmd'], 'status': 'error', 'error_msg':'pad name does not exist', 'ts': g_ts}))
                return
            data_len = len(g_pads[msg['pad_name']]['data']['dict'])
            await ws.send(json.dumps({'cmd':msg['cmd'],'status':'ok','ts':g_ts, 'len':data_len}))
        elif msg['cmd']=='getAll':
            if msg['pad_name'] not in g_pads['pads']:
                await ws.send(json.dumps({'cmd': msg['cmd'], 'status': 'error', 'error_msg':'pad name does not exist', 'ts': g_ts}))
                return
            await ws.send(json.dumps({'cmd':msg['cmd'],'status':'ok','ts':1, 'data':getdata(msg['pad_name'])}))
        elif msg['cmd']=='replace':
            if msg['pad_name'] not in g_pads['pads']:
                await ws.send(json.dumps({'cmd': msg['cmd'], 'status': 'error', 'error_msg':'pad name does not exist', 'ts': g_ts}))
                return
            print('replace:', msg['data'])
            replacedata(msg['pad_name'],msg['data'])

            for i in g_pads['pads'][msg['pad_name']]['ws']:
                try:
                    await i.send(json.dumps({'cmd':msg['cmd'], 'status':'ok', 'ts':g_ts, 'data':msg['data']}))
                except:
                    print('something error happen. just remove the ws', ws)
                    i.close()









#=======================
#async def consumer(websocket,message):
#    cmd_parse(websocket,message)


async def consumer_handler(websocket):
    while True:
        try:
            message = await websocket.recv()
            await consumer(websocket, message)
        except  websockets.exceptions.ConnectionClosed:
            remove_ws(websocket)
            return
        except concurrent.futures._base.CancelledError:
            print ('cancel concurrent. ws remove?')
            return
        except :
            print("Unexpected error:", sys.exc_info())
            print('something error happen. just close socket=%s', websocket)
            remove_ws(websocket)
            return

#
# async def producer_handler(websocket):
#     while True:
#         try:
#             message = await producer(websocket)
#             if message!=None:
#                 await websocket.send(message)
#         except  websockets.exceptions.ConnectionClosed:
#             remove_ws(websocket)
#             return
#         except concurrent.futures._base.CancelledError:
#             print ('cancel concurrent. ws remove?')
#             return
#         except:
#             print("Unexpected error:", sys.exc_info()[0])
#             print('something error happen. just close socket=%s', websocket)
#             remove_ws(websocket)
#             return

async def handler(websocket, path):
    add_ws(websocket)
    await consumer_handler(websocket)


start_server = websockets.serve(handler, '127.0.0.1', 11234)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

