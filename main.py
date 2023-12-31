import os
import time
import decky_plugin
import asyncio
from pathlib import Path
import sqlite3
from collections import defaultdict


bat_paths = {
            'power':'/sys/class/power_supply/BAT0/power_now',
            'capacity':'sys/class/power_supply/BAT0/capacity',
            'status':'/sys/class/power_supply/BAT0/status'
            }

bat_status = {
        'Charging' : 1,
        'Discharging' : -1,
        }

data_capture_interval = 5

'''
def split_by_app(data):
    idxs = []
    start_idx = 0
    app = data[0][-1]
    for idx, d in enumerate(data):
        if d[4] != app:
            idxs.append((start_idx, idx - 1, app))
            start_idx = idx
            app = d[-1]
    if start_idx != idx:
        idxs.append((start_idx, idx, app))
    return idxs
'''


"""
select count(*) from battery where time > (select time from battery where status=1 order by time desc LIMIT 1);
"""

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
            
            def get_data_for_graph(end_time, start_time):
                decky_plugin.logger.info("get_data_for_graph") 
                data = self.cursor.execute(
                        "select * from battery where time > %i"%start_time
                        ).fetchall()
                diff = end_time - start_time
                x_axis = [(d[0] - start_time) / diff for d in data]
                y_axis = [d[1] / 100 for d in data]
                return x_axis, y_axis    

            def get_avg_by_app(end_time, start_time):
                decky_plugin.logger.info("get_avg_by_app") 
                data = self.cursor.execute(
                        """select replace(app,'Unknown','Steam') as app,round(AVG(power),1) as power 
                            from battery where status == -1 and time > %i 
                            group by app,status order by power desc"""%start_time
                        ).fetchall()
                per_app_data = [{"name": d[0], "average_power": d[1]} for d in data]
                return per_app_data  

            end_time = time.time()
            start_time = end_time - 24 * lookback * 3600 

            '''
            data = self.cursor.execute(
                "select * from battery where time > " + str(int(start_time))
            ).fetchall()
            diff = end_time - start_time
            x_axis = [(d[0] - start_time) / diff for d in data]
            y_axis = [d[1] / 100 for d in data]
            '''
            x_axis, y_axis = get_data_for_graph(end_time, start_time)

            """
            per_app_powers = defaultdict(list)
            for start, end, app in split_by_app(data):
                if app == "Unknown":
                    app = "Steam"
                per_app_powers[app].extend(
                    [d[3] / 1.0 for d in data[start:end] if d[2] == -1]
                )
            per_app_data = [
                {"name": app, "average_power": int(sum(power_data) / len(power_data))}
                for app, power_data in per_app_powers.items()
                if power_data
            ]"""
            per_app_data = get_avg_by_app(end_time, start_time)
            return {
                "x": x_axis,
                "cap": y_axis,
                "power_data": per_app_data 
                #sorted(per_app_data, key=lambda x: -x["average_power"]),
            }
        except Exception:
            decky_plugin.logger.exception("could not get recent data")

    async def recorder(self):

        '''
        #volt_file = open("/sys/class/power_supply/BAT1/voltage_now")
        #curr_file = open("/sys/class/power_supply/BAT1/current_now")
        power_file = open("/sys/class/power_supply/BAT0/power_now")
        cap_file = open("/sys/class/power_supply/BAT0/capacity")
        status = open("/sys/class/power_supply/BAT0/status")
        '''
        logger = decky_plugin.logger
        files = {}
        for item in bat_paths.items():
            files[item[0]] = open(item[1])

        logger.info("recorder started")
        running_list = []
        while True:
            try:
                for item in files.items():
                    f = item[1]
                    val = f.seek(0).read().strip()
                    match item[0]:
                        case 'power':
                            power = int(val)*10**-6
                        case 'capacity':
                            cap = int(val)
                        case 'status':
                            if val in bat_status:
                                status = bat_status[val]
                            else:
                                status = 0


                '''  
                #volt_file.seek(0)
                #curr_file.seek(0)
                power_file.seek(0)
                cap_file.seek(0)
                status.seek(0)
                #volt = int(volt_file.read().strip())
                #curr = int(curr_file.read().strip())
                power = int(power_file.read().strip())*10**-6
                cap = int(cap_file.read().strip())
                stat = status.read().strip()
                if stat == "Discharging":
                    stat = -1
                elif stat == "Charging":
                    stat = 1
                else:
                    stat = 0

                #power = int(volt * curr * 10.0**-11)
                '''
                curr_time = int(time.time())
                running_list.append((curr_time, cap, stat, power, self.app))
                if len(running_list) > 10:
                    self.cursor.executemany(
                        "insert into battery values (?, ?, ?, ?, ?)", running_list
                    )
                    self.con.commit()
                    running_list = []
            except Exception:
                logger.exception("recorder")
            await asyncio.sleep(data_capture_interval)
