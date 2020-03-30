import json
import logging
from dateutil.parser import isoparse
from datetime import datetime, timedelta
from collections import deque
from receiver import log_folder, log_filepath, notes_in_minute
from file_read_backwards import FileReadBackwards

log_formatter = logging.Formatter("%(asctime)s\t%(levelname)s\t%(message)s")
handler_file = logging.FileHandler(filename = log_folder+"debug.log")
handler_file.setFormatter(log_formatter)

logger = logging.getLogger()
logger.addHandler(handler_file)

handler_file.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)

DEBUG_DATE_NOW = isoparse("2020-03-29T02:49:33.792004")

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

        now = DEBUG_DATE_NOW if DEBUG_DATE_NOW else datetime.now() ###
        border = (now - timedelta(minutes=minutes)).timestamp()
        
        logger.debug("")
        logger.debug("-"*80)
        logger.debug("Started filling TempAnalytics:")
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
        logger.debug("-"*80)
    
    def __str__(self):
        show_notes = 5 * notes_in_minute
        strs = "The last {} notes in analytics:\n".format(show_notes)

        for linenum in range(show_notes):
            line = self.notes[linenum]
            strs += str(line) + f' - {self.minutes_elapsed(line["timestamp"])} min ago.\n'
        return strs


    def check_tendency(self, last_minutes = 10):
        """Проверит, были тенденции к изменению температуры 
        за последние <last_minutes> минут. Значение "0" - проверка
        всех записей.

        Определим исследуемый участок, возьмем среднее за 1-2 самые 
        старые минуты участка как исходную температуру. Пройдем по участку, 
        определяя нарушения <_temp_delta>. Отсеим случайные нарушения (среднее по ближайшим). 
        Будем вести список нарушений по приросту/убыванию температуры и время нарушения. 
        Определим пиковые значения (отрицательные и положительные) и их время. 
        Определим среднее за 1-2 самые свежие минуты как текущую температуру.

        Решение по тенденции изменения: исходная-текущая -- если в норме, OK
        если тенденции к изменению есть - оповещаем пиковыми значениями.  
        нет. 
        Если есть пиковые значения - оповещаем.      
        """
        logging.debug(f'Current time is {(DEBUG_DATE_NOW if DEBUG_DATE_NOW else datetime.now()).isoformat()}.')
        logging.debug(f"Trying to find records made in {last_minutes} minutes.")
        latest_index = -1
        for index in reversed(range(last_minutes*notes_in_minute if len(self.notes) > last_minutes*notes_in_minute else len(self.notes))): # десятиминутные логи должны быть где-то в тех краях. Будем от этого спускаться к более свежим, пока не найдем десятиминутный, Поправил т.к. упирался в размер списка при малом количестве записей
            
            logging.debug(f"checking: index {index}/{len(self.notes)-1}.")
            if self.minutes_elapsed(self.notes[index]["timestamp"]) <= last_minutes:
                latest_index = index # нашли
                break
        if latest_index < notes_in_minute*2:
            logger.warning(f'Tendency checking ({last_minutes} min) failed: Too small records count to analyze ({latest_index + 1}).')
            return {"error": True}
        
        start_temp = .0
        end_temp = .0

        # вычислим start_temp
        for _ in range(latest_index,latest_index-notes_in_minute, -1):
            start_temp += self.notes[_]["temperature"]
        start_temp = round(start_temp/notes_in_minute, 2)
        logging.debug(f'Start temp: {start_temp}')
        # вычислим end_temp
        for _ in range(0, notes_in_minute):
            end_temp += self.notes[_]["temperature"]
        end_temp = round(end_temp/notes_in_minute, 2)
        logging.debug(f'End temp: {end_temp}')

        # заполним значениями с отсечением ошибок (округление с соседними)
        warnings = []
        for _ in range(0, latest_index-notes_in_minute):
            if abs(self.notes[_]["temperature"] - start_temp) >= self._temp_delta: # подозрение на нарушение
                logger.debug(f'Can be warning: {self.notes[_]} against {start_temp}.')
                correct_temp = .0
                for ss in range(_- int(notes_in_minute/2),_+int(notes_in_minute/2)+1): # возьмем соседние
                    correct_temp += self.notes[ss]["temperature"]
                correct_temp = round(correct_temp/notes_in_minute,2)
                if abs(correct_temp-start_temp) >=self._temp_delta: # подтверждено
                    warnings.append([round(correct_temp-start_temp,2), self.notes[_]])
                    logger.info(f'Temperature {correct_temp} is over delta ({correct_temp}/{start_temp}) at {datetime.fromtimestamp(self.notes[_]["timestamp"])}')
                else:
                    logger.debug(f'Its OK, {correct_temp} anainst {start_temp}.')

        # определим максимумы    
        if len(warnings) > 0:
            warnings_to_send = {}
            for warn in warnings:
                if warn[0] > 0:
                    if not warnings_to_send.get("over") or warn[0] > warnings_to_send["over"][0]:
                        warnings_to_send["over"] = warn
                else:
                    if not warnings_to_send.get("lover") or warn[0] < warnings_to_send["lover"][0]:
                        warnings_to_send["lover"] = warn            
        

    def minutes_elapsed(self, unixtime):        
        now = DEBUG_DATE_NOW if DEBUG_DATE_NOW else datetime.now() ###
        delta = now - datetime.fromtimestamp(unixtime)

        return int(delta.seconds / 60)

    def put(self, note):
        """
        В идеале, должен принимать dict(), но может и парсить строковый JSON.
        Положит новую запись в начало очереди, отсечёт устаревшие записи с конца.
        """
        logger.debug(f'Trying to append: {note}.')
        if type(note) != dict:
            logger.warning(f'TempAnalyzer.put() received non-dict object. Parsing...')
            try:
                note = json.loads(note)
                logger.warning(f'OK')
            except json.decoder.JSONDecodeError as ex:
                logger.error("Failed parsing JSON in TempAnalyzer.put() method.")
                return

        try:
            note["timestamp"] = isoparse(note["timestamp"]).timestamp()
            self.notes.appendleft(note)
            logger.info(f"Appended: {note}.")
        except KeyError as ex:
            logger.error(f'Caught Exception: "{ex}" in parsing or appending note.')
        while len(self.notes) > 0 and self.minutes_elapsed(self.notes[-1]["timestamp"]) > self._oldest_minutes:
            tmp = self.notes.pop()
            logger.debug(f'Deleted overtimed ({self.minutes_elapsed(tmp["timestamp"])}/{self._oldest_minutes} min) note: {tmp}.')

if __name__ == "__main__":    
    TA = TempAnalytics()
    TA.check_tendency(10)    
