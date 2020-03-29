import json
from dateutil.parser import isoparse
from datetime import datetime, timedelta
from receiver import log_filepath
from file_read_backwards import FileReadBackwards

def fill_analytics(minutes = 30):
    """
    Заполнит систему предыдущими значениями (за последние полчаса по-умолчанию)
    если такие имеются.
    """
    border = datetime.now() - timedelta(minutes=minutes)
    with FileReadBackwards(log_filepath, encoding="utf-8") as logfile:
        readed = 0
        for line in logfile:
            data = json.loads(line)
            data_ts = isoparse(data["timestamp"])
            if data_ts < border:
                break            
            print(line)
            readed += 1
        print("Analytics filled with {notes} notes of the last {minutes} minutes.".format(
            notes=readed, minutes = minutes))


if __name__ == "__main__":
    fill_analytics()