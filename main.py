import os
import time
import decky_plugin
import asyncio
from pathlib import Path
import sqlite3
from collections import defaultdict
import datetime


data_capture_interval = 5


class Plugin:
    async def _main(self):
        try:
            self.app = "Unknown"
            decky_plugin.logger.info("steam deck battery logger _main")
            battery_db = Path(decky_plugin.DECKY_PLUGIN_RUNTIME_DIR) / "battery.db"
            database_file = str(battery_db)
            self.con = sqlite3.connect(database_file)
            self.cursor = self.con.cursor()
            tables = self.cursor.execute(
                "select name from sqlite_master where type='table';"
            ).fetchall()
            if not tables:
                decky_plugin.logger.info("Creating database table for the first time")
                self.cursor.execute(
                    "create table battery (time __integer, capacity __integer, status __integer, power __integer, app __text);"
                )
                self.con.commit()

            loop = asyncio.get_event_loop()
            self._recorder_task = loop.create_task(Plugin.recorder(self))
            decky_plugin.logger.info("steam deck battery logger _main finished")
        except Exception:
            decky_plugin.logger.exception("_main")

    async def _unload(self):
        decky_plugin.logger.info("steam deck battery logger _unload")
        pass

    async def set_app(self, app: str = "Unknown"):
        decky_plugin.logger.info(f"Getting app as {app}")
        if app:
            self.app = app
        return True

    async def get_recent_data(self, lookback=2):
        try:
            decky_plugin.logger.info(f"lookback {lookback}")

            def get_battery_sessions(end_time, start_time):
                decky_plugin.logger.info("get_battery_sessions")
                data = self.cursor.execute(
                        """select time,prev_status,status,capacity from 
                            ( select time,app,status,capacity,lag(status,1) over () as prev_status, 
                            sum(status) over (order by time asc rows between 1 preceding and current row) as sum_status from battery where time > %i) 
                            where sum_status between 0 and 1"""%start_time).fetchall()
                sessions = []
                session = {}
                is_start = False
                for item in data:
                    if (item[2] == -1) & (is_start == False):
                        is_start = True
                        session['start'] = item[0]
                        session['end'] = end_time
                        continue
                    if (item[2] != -1) & (is_start == True):
                        session['end'] = item[0]
                        sessions.append(session)
                        is_start = False
                        session = {}
                sessions_info = []
                sessions.reverse()
                for session in sessions:
                    session_info = get_esimated_screen_time(session)
                    sessions_info = sessions_info+session_info
                return sessions_info
            
            def get_data_for_graph(end_time, start_time):
                decky_plugin.logger.info("get_data_for_graph") 
                data = self.cursor.execute(
                        """select time, capacity, prev_capacity, status from (select time, capacity, 
                        lag(capacity,1) over() as prev_capacity, status from battery where time>%i) 
                        where capacity <> prev_capacity"""%start_time
                        #"select * from battery where time > %i"%start_time
                        ).fetchall()
                diff = len(data)#end_time - start_time
                x_axis = [x/(diff-1) for x in range(diff)]
                #[(d[0] - start_time) / diff for d in data]
                y_axis = [d[1] / 100 for d in data]
                colors = { -1: 'rgba(204,51,0,0.4)',
                            1: 'rgba(51,204,51,0.4)',
                            2: 'rgba(255,153,0,0.4)'}
                strokeStyle = [colors[d[3]] for d in data]
                return x_axis, y_axis, strokeStyle    

            def get_avg_by_app(end_time, start_time):
                decky_plugin.logger.info("get_avg_by_app") 
                data = self.cursor.execute(
                        """select replace(app,'Unknown','Steam') as app,round(AVG(power),1) as power 
                            from battery where status == -1 and time > %i 
                            group by app,status order by power desc"""%start_time
                        ).fetchall()
                max_len = 21
                per_app_data = [{"name": d[0].ljust(max_len, '\t')[:max_len], 
                                "average_power": '%s Wh'%d[1]} for d in data]
                return per_app_data  

            def get_esimated_screen_time(session):
                decky_plugin.logger.info("get_esimated_screen_time") 
                data = self.cursor.execute(
                    """select count(*), max(capacity), min(capacity), round(AVG(power),1) from battery 
                        where time between %i and %i"""%(session['start'], session['end'])
                        ).fetchall()
                
                if int(data[0][0]) > 0:
                    start_session = str(datetime.datetime.fromtimestamp(session['start']))
                    estimated_time = str(datetime.timedelta(seconds = int(data[0][0])*data_capture_interval))
                    max_cap, min_cap, avg = data[0][1], data[0][2], data[0][3]
                    return [{"name":'%s'%start_session, "average_power": '\n%i%%->%i%% | %s Wh | %s'%(max_cap, min_cap, avg, estimated_time)}]
                else:
                    return []
                

            end_time = time.time()
            start_time = end_time - 24 * lookback * 3600 

            x_axis, y_axis, strokeStyle = get_data_for_graph(end_time, start_time)   
            per_app_data = get_avg_by_app(end_time, start_time)
            per_session_data = get_battery_sessions(end_time, start_time)
            return {
                "x": x_axis,
                "cap": y_axis,
                "strokeStyle" : strokeStyle,
                "power_data": per_app_data, 
                "session_data": per_session_data
                
            }
        except Exception:
            decky_plugin.logger.exception("could not get recent data")

    async def recorder(self):

        bat_paths = {
                    'power':'/sys/class/power_supply/BAT0/power_now',
                    'capacity':'/sys/class/power_supply/BAT0/capacity',
                    'status':'/sys/class/power_supply/BAT0/status'
                    }

        bat_status = {
                'Charging' : 1,
                'Discharging' : -1,
                }


        logger = decky_plugin.logger
        logger.info("recorder started")
        files = {}
        for item in bat_paths.items():
            files[item[0]] = open(item[1])

        logger.info("files opened")
        running_list = []
        while True:
            try:
                for item in files.items():
                    f = item[1]
                    val = f.read().strip()
                    f.seek(0)
                    match item[0]:
                        case 'power':
                            power = int(val)*10**-6
                        case 'capacity':
                            cap = int(val)
                        case 'status':
                            if val in bat_status.keys():
                                status = bat_status[val]
                            else:
                                status = 2


                curr_time = int(time.time())
                running_list.append((curr_time, cap, status, power, self.app))
                if len(running_list) > 10:
                    logger.info("data ready to insert")
                    self.cursor.executemany(
                        "insert into battery values (?, ?, ?, ?, ?)", running_list
                    )
                    self.con.commit()
                    logger.info("data inserted")
                    running_list = []
            except Exception:
                logger.exception("recorder")
            await asyncio.sleep(data_capture_interval)
