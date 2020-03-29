import json
from dateutil.parser import isoparse
from datetime import datetime, timedelta
from receiver import log_filepath
from file_read_backwards import FileReadBackwards

class TempAnalytics:
    """
Класс должен внутри себя держать данные за последние <_oldest_minutes> минут,
при дополнении новыми записями - освобождать самые старые.
Каждые <_rescan_minutes> перепроверять события:
- превышен ли допустимый предел отклоненияя температуры <_temp_delta> 
за последние list(<10> <30> <60> <120> <all>) минут
- допустимая погрешность измерений датчика будет <_inacc> градуса
- в записях время записи будет храниться в формате UNIX-time (секунды с начала эпохи)
для более быстрого сравнения
    """
    _oldest_minutes = 20#60*4
    _rescan_minutes = 5
    _temp_delta = 2
    _timers = [10, 30, 60, 120]
    _inacc = 0.5

    notes = []

    def __init__(self, filepath = log_filepath, minutes = _oldest_minutes):
        """Заполнит систему предыдущими значениями (за последние 4 часа по-умолчанию)
        если такие имеются.
        """
        border = (datetime.now() - timedelta(minutes=minutes)).timestamp()
        with FileReadBackwards(log_filepath, encoding="utf-8") as logfile:
            readed = 0
            errors = 0
            for line in logfile:
                parsed_line = json.loads(line)
                parsed_line["timestamp"] = isoparse(parsed_line["timestamp"]).timestamp() # ISO8601 преобразуем в UNIX-time
                if parsed_line["timestamp"] < border:
                    break
                if parsed_line['error']: # не учитываем ошибки чтения с датчика
                    errors += 1
                else:
                    self.notes.append(parsed_line)
                    readed += 1
            self.notes.reverse()
            print("Analytics filled with {notes} notes of the last {minutes} minutes.\nErrors: {errors}.".format(
                notes = readed, minutes = minutes, errors = errors))
            for note in self.notes:
                print(note)


if __name__ == "__main__":
    TA = TempAnalytics()