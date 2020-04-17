import os
from dateutil.parser import isoparse
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from file_read_backwards import FileReadBackwards
import json
from receiver import notes_in_minute, log_filepath


def load_jsonfile_arglists(filepath, *args, backwards = False, count = 0):
	"""Function can help you to parse """
	output_lists = { arg: [] for arg in args }
	openfunc = FileReadBackwards if backwards else open
	with openfunc(filepath, encoding="UTF-8") as file:
		if not count:
			## push all the values
			for line in file:
				parsed_line = json.loads(line)
				if parsed_line["error"]: #specific
					continue
				for arg in args:
					output_lists[arg].append(parsed_line[arg])
		else:
			for index, line in enumerate(file, start=1):
				if index > count:
					break
				parsed_line = json.loads(line)
				if parsed_line["error"]: #specific
					continue
				for arg in args:
					output_lists[arg].append(parsed_line[arg])
	if not backwards:
		## to restore original order -- list.append() puts new value to the end
		for values_list in output_lists.values():
			values_list.reverse()

	return [output_lists[arg] for arg in args]


def makeplot_datetime(filename, values_time, values_y):
	axes = plt.gca()
	axes.grid(True) # set grid
	axes.set_ylim([19.0, 30.0])

	lazy_intervals = {
		0: 5, # < 1 hour -- tick every 5 minutes
		1: 10, # < 2 hour -- tick every 10 minutes
		2: 20, # < 3 hour -- tick every 20 minutes
		3: 20, # < 3 hour -- tick every 20 minutes
		4: 30}
	
	interval = lazy_intervals.get(int(len(values_time) / (notes_in_minute*60)), 60) # calculate tick interval

	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
	plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=interval))


	plt.plot(values_time, values_y)
	# plt.gcf().autofmt_xdate() # italic datetime
	
	filepath = filename + '.png'
	plt.savefig(filepath)
	return filepath


def filter_values(values, max_delta=0.5):
	"""Can fix seldom occurrences of deviant values."""
	deltas = [abs(values[x]-values[x+1]) for x in range(len(values)-1)] # without the last value

	if deltas[0] > max_delta and deltas[1] < max_delta: # error in the first item
		print(f'Error in [0] -- {values[0]}!, {values[1]}, {values[2]}')
		values[0] = values[1]
	if deltas[-1] > max_delta and deltas[-2] < max_delta: # error in the last
		print(f'Error in [-1] -- {values[-3]}, {values[-2]}, {values[-1]}!')
		values[-1] = values[-2]
	
	for _, delta in enumerate(deltas[1:], start=1):
		if delta > max_delta and deltas[_-1] > max_delta:
			print(f'Error in [{_}] -- {values[_-1]}, {values[_]}!, {values[_+1]}')
			values[_] = (values[_-1] + values[_+1]) / 2


def create_plotfile(folder = "./plots/", last_hours=4):
	if not os.path.exists(folder):
		os.makedirs(folder)

	time, temp = load_jsonfile_arglists(log_filepath, "timestamp", "temperature", 
				 backwards=True, count=notes_in_minute*60*last_hours)
	
	filter_values(temp)
	time_dt = list(map(isoparse, time))

	return makeplot_datetime(folder+time[-1]+f'_{last_hours}hours', time_dt, temp)


if __name__ == "__main__":
	print(create_plotfile())
