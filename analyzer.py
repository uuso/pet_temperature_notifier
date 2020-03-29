import json
import logging
from dateutil.parser import isoparse
from datetime import datetime, timedelta
from collections import deque
from receiver import log_folder, log_filepath, notes_in_minute
from file_read_backwards import FileReadBackwards

log_formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")
handler_file = logging.FileHandler(filename = log_folder+"debug.log")  # -- file
handler_file.setFormatter(log_formatter)

logger = logging.getLogger()
logger.addHandler(handler_file)

handler_file.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)


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
    _oldest_minutes = 60*4
    _rescan_minutes = 5
    _temp_delta = 2
    _timers = [10, 30, 60, 120]
    _inacc = 0.5

    notes = deque()

    def __init__(self, filepath = log_filepath, minutes = _oldest_minutes):
        """Заполнит систему предыдущими значениями (за последние 4 часа по-умолчанию)
        если такие имеются.
        """
        border = (datetime.now() - timedelta(minutes=minutes)).timestamp()
        logger.debug(f"Started filling TempAnalytics:")
        logger.debug(f"_oldest_minutes: {self._oldest_minutes}, _rescan_minutes: {self._rescan_minutes},")
        logger.debug(f"_temp_delta: {self._temp_delta}, _timers: {self._timers}, _inacc: {self._inacc}.")
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
                    
            logger.info("Analytics filled with {notes} notes of the last {minutes} minutes. Errors: {errors}.".format(
                notes = readed, minutes = minutes, errors = errors))

            # for note in self.notes:
            #     ts = note.pop("timestamp")
            #     print("{} ago.\t{}".format(datetime.now() - datetime.fromtimestamp(ts), note))
            # print(self.notes[0])
    
    def __str__(self):
        show_notes = 10 # если указать 0 - выведет все записи
        strs = "The last {} notes in analytics:\n".format(show_notes if show_notes else len(self.notes))

        # for lines in self.notes[-show_notes:]:
        #     strs += str(lines) + '\n'

        for linenum in range(show_notes):
            line = self.notes[linenum]
            strs += str(line) + f' - {self.minutes_elapsed(line["timestamp"])} min ago.\n'
        return strs


    def check(self, last_minutes = 10):
        """Проверит, были тенденции к изменению температуры 
        за последние <last_minutes> минут. Значение "0" - проверка
        всех записей.
        """
        return 0


    def minutes_elapsed(self, unixtime):
        delta = datetime.now() - datetime.fromtimestamp(unixtime)
        return int(delta.seconds / 60)

    def put(self, note):
        logger.debug(f"Trying to append: {note}.")
        self.notes.appendleft(note)
        logger.info(f"Appended: {note}.")
        while self.minutes_elapsed(self.notes[-1]["timestamp"]) > self._oldest_minutes:
            tmp = self.notes.pop()
            print(type(tmp))
            # logger.debug(f"Deleted overtimed note: {tmp} - {self.minutes_elapsed(tmp["timestamp"])} min.")

if __name__ == "__main__":    
    print(TempAnalytics())