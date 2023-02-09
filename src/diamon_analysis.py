import numpy as np
import pandas as pd
#issue with scipy - cant import lib?
from scipy.signal import find_peaks
import pickle

def save_pickle(data, name):
    """
    Saves pickled data to file. (less memory)
    """
    with open(name, 'wb') as f:
        pickle.dump(data, f)

def load_pickle(name):
    """
    load pickled data from file into program
    """
    with open(name, 'rb') as f:
        return pickle.load(f)

def filter_location(data, building):
    """
    filter data if both ts1 & ts2 read in into separate dictionaries based on reference
    Args:
        data (dict): all ts1 ts2 data
        building (string): selected building to filter

    Returns:
        _type_: _description_
    """
    #match the variable building to the string - building
    match building:
        case "TS1":
            ts1_dict = {key: dic for key, dic in data.items() if (
                dic["reference"]["Measurement Reference"].iloc[0][0] == '1')} 
            return ts1_dict
        case "TS2":
            ts2_dict = {key: dic for key, dic in data.items() if (
                dic["reference"]["Measurement Reference"].iloc[0][0] == '2')}
            return ts2_dict

def ts2_beamline_names():
    """
    returns a list of beamline names in ts2
    """
    return ["chipir", "sans2d", "wish", 
                "inter", "offspec", "let", 
                "nimrod", "polref", "zoom", "larmor", 
                "imat", "epb"]

def convert_to_df(data):
    """Filter out any low energy recordings for high energy unfold data
    returns a dataframe
    
    STEVE - filter using enum 
    """
    beam_df = {}
    for beamline in ts2_beamline_names():
        series_list = []
        for measurement in data.values():
            ref = measurement["reference"]["Measurement Reference"].iloc[0]
            match beamline:
                case "chipir":
                    if ref[1] == "C":
                        series_list.append(convert_to_ds(measurement))
                case "imat":
                    if ref[1] == "I":
                        series_list.append(convert_to_ds(measurement))
                case "inter":
                    if ref[1:3] == "In":
                        series_list.append(convert_to_ds(measurement))
                case "larmor":
                    if ref[1] == "L":
                        series_list.append(convert_to_ds(measurement))
                case "let":
                    if ref[1:3] == "le":
                        series_list.append(convert_to_ds(measurement))
                case "nimrod":
                    if ref[1] == "N":
                        series_list.append(convert_to_ds(measurement))
                case "offspec":
                    if ref[1] == "O":
                        series_list.append(convert_to_ds(measurement))
                case "polref":
                    if ref[1] == "P":
                        series_list.append(convert_to_ds(measurement))
                case "sans2d":
                    if ref[1] == "S":
                        series_list.append(convert_to_ds(measurement))
                case "wish":
                    if ref[1] == "W":
                        series_list.append(convert_to_ds(measurement))
                case "zoom":
                    if ref[1] == "Z":
                        series_list.append(convert_to_ds(measurement))
                case "epb":
                    if ref[1] == "B":
                        series_list.append(convert_to_ds(measurement))
        beam_df[beamline] = pd.DataFrame(series_list)
        if not beam_df[beamline].empty:
            beam_df[beamline] = beam_df[beamline].sort_values("distance")
    return beam_df


def convert_to_ds(dic):
    """
    Convert list of labels and the data into a pandas series
    Args:
        dic (dict) : all data for one measurement

    Returns:
        dseries
    """
    labels = ("file_name", "start", "end", "reference", "x", "y", "z", "dose_rate", "norm_dose",
              "dose_rate_uncert", "dose_area_product", "dose_area_prod_uncert", "thermal","epi", "fast", "phi", 
              "phi_uncert", "D1", "D2", "D3", "D4", "D5", "D6", "F", "FL", "FR", "R", "RR", "RL", 
              "energy_bins", "flux_bins")

    # the unfold data - summary of diamon data in high or low energy mode 
    # filter for high or low energy
    if "high_e" in dic.keys():
        unfold_data = dic["high_e"]
    elif "low_e" in dic.keys():
        unfold_data = dic["low_e"]

    data_list = [dic["name"], dic["datetime"]["start"], dic["datetime"]["end"], 
                 dic["reference"]["Measurement Reference"].iloc[0], 
                 dic["reference"]['x'].iloc[0], dic["reference"]['y'].iloc[0], 
                 dic["reference"]['z'].iloc[0], unfold_data["dose_rate"], dic["out"]["norm_dose"].iloc[-1],
                 unfold_data["dose_rate_uncert"], 
                 unfold_data["dose_area_product"], unfold_data["dose_area_product_uncert"], 
                 unfold_data["thermal"], unfold_data["epi"], unfold_data["fast"], 
                unfold_data["phi"], unfold_data["phi_uncert"], unfold_data["count_D1"], 
                unfold_data["count_D2"], unfold_data["count_D3"], unfold_data["count_D4"], 
                unfold_data["count_D5"], unfold_data["count_D6"], unfold_data["count_F"], 
                unfold_data["count_FL"], unfold_data["count_FR"], unfold_data["count_R"], 
                unfold_data["count_RR"], unfold_data["count_RL"], 
                unfold_data["energy_bins"], unfold_data["flux_bins"]]

    s1 = pd.Series(data_list, index=labels)
    # call function to find 2d distance
    s1 = get_distance(s1)
    return s1

def convert_status_to_ds(dic):
    """
    basic data info put into a panda series (name, coordinates, location)
    Args:
        dic (dict): dictionary of all diamon data

    Returns:
        s1 - panda series: series containing key info
    """
    labels = ("file_name", "start", "end", "reference", "x", "y", "z")

    data_list = [dic["name"], dic["datetime"]["start"],  dic["datetime"]["end"],
                 dic["reference"]["Measurement Reference"].iloc[0],
                 dic["reference"]['x'].iloc[0], dic["reference"]['y'].iloc[0],
                 dic["reference"]['z'].iloc[0]]

    s1 = pd.Series(data_list, index=labels)
    s1 = get_distance(s1)
    return s1

def get_distance(data, dimension=2):
    """
    get 2d and 3d pythag distance between coordinates and the origin
    Args:
        data (panda series): series containing diamon data
        dimension (int, optional): 2d or 3d dimension. Defaults to 2.

    Returns:
        data (series): data with distance column added
    """
    if dimension == 2:
        data['distance'] = np.sqrt(data['x']**2 + data['y']**2)
    elif dimension == 3:
        data['distance'] = np.sqrt(data['x']**2 + data['y']**2 + data['z']**2)
    return data

def combine_continuous_data_files(dataframes, cum_time=None):
    """
    This function allows repeated measurements in the same location to be conjoined
    into one datafame

    Args:
        dataframes (panda df):
        cum_time (boolean, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    combined_dataframe = []
    for i, dataframe in enumerate(dataframes):

        if cum_time and i != 0:
            last_index = dataframes[i-1].iloc[-1,0]
            #this aligns the new files time with the previous so they are adjacent
            dataframe.iloc[:,0] = last_index + dataframe.iloc[:,0]

        combined_dataframe.append(dataframe)
    combined_dataframe = pd.concat(combined_dataframe, ignore_index=True)

    return combined_dataframe

def select_high_energy(data):
    """
    Select high energy data from files - ignore F_unfold - low diamon energy mode
    Args:
        data (dict): diamon data

    Returns:
        dict: returns data with only high energy data included
    """
    return  {data_key: date for data_key, date in data.items() for key in date.keys()  if "high_e" in key}

def average_daily_data(unfold_data):
    """
    extracts the average flux across group of measurements
    Args:
        unfold_data (_type_): _description_

    Returns:
        _type_: _description_
    """
    fluxes = []
    for data in unfold_data:
        _, flux = extract_spectrum(data)
        if np.average(flux) > 1e-10:
            fluxes.append(flux)
    avg_flux = np.average(fluxes, axis=0)
    return avg_flux

def extract_spectrum(data):
    """
`   get the flux and enegry bins from unfold data
    Args:
        data (series/df): contains unfold file data

    Returns:
        2 arrays for flux and energy
    """
    energy = data["energy_bins"]
    flux = data["flux_bins"]
    return energy, flux

def peaks_finder(data):
    """
    find the peak of spectrum and extract energy and flux
    Args:
        data (series)_
    Returns:
        2 arrays of peak flux and energy for three regions
    """
    
    energy, flux = np.array(extract_spectrum(data))
    #border threshold to reflect change in signal
    
    flux_peaks_i , flux_peaks = find_peaks(flux, height=0, prominence=0.0001)
    flux_peaks = flux_peaks["peak_heights"]

    energy_peaks = energy[(flux_peaks_i)]
    return flux_peaks, energy_peaks

def convert_date_to_string(dt):
    """
    convert a numpy datetime64 object to string (str is necessary) as np returns a np.str class
    Args:
        dt (numpy datetime object)
    Returns:
        str
    """
    return str(np.datetime_as_string(dt))

def get_names(data):
    """
    get building and beamline name as list of str
    Args:
        data (df): df of measurement location reference

    Returns:
        list: str
    """
    #extracts a code reference format : 2ZT-3 : ts2, zoom, top, 3rd measurement
    ref = data["Measurement Reference"].iloc[0]
    
    if ref[0] == "2":
        if ref[1] == "C":
            return ["ts2", "chipir"]
        elif ref[1] == "I":
            return ["ts2", "imat"]
        elif ref[1:3] == "In":
            return ["ts2", "inter"]
        elif ref[1] == "L":
            return ["ts2", "larmor"]
        elif ref[1:3] == "le":
            return ["ts2", "let"]
        elif ref[1] == "N":
            return ["ts2", "nimrod"]
        elif ref[1] == "O":
            return ["ts2", "offspec"]
        elif ref[1] == "P":
            return ["ts2", "polref"]
        elif ref[1] == "S":
            return ["ts2", "sans2d"]
        elif ref[1] == "W":
            return ["ts2", "wish"]
        elif ref[1] == "Z":
            return ["ts2", "zoom"]
        elif ref[1] == "B":
            return ["ts2", "epb"]
    elif ref[0] == "1":
        return ["ts1", "null"]

def get_query_info(data, time):
    """
    get shutter status at most recent time since the selected time
    Args:
        data (df): shutter df indexed by datetime
        time (datetime object): time of recordingdatetime

    Returns:
        boolean: true if shutter open (2), false if shutter closed/setup (1/3)
    """
    #extract the tail of df where shutter df matches previous times
    status = data[data.index < time].tail(1)["_value"].values[0]
    if status == 1:
        return False
    if status == 2:
        return True
    if status == 3:
        return False

def get_current_info(data, current_df):
    """
    extract current information from time of data
    Args:
        data (dict): diamon data
        current (df): df of current data

    Returns:
        list: list of current data
    """
    times = data["out"]["datetime"]
    currents = []
    #loop over every timestamp in diamon recording
    for i, time in enumerate(times):
        #first measurement take last data 20s before
        if i ==0:
            start = times.values[i] - np.timedelta64(20, 's')
        else:
            #take start as value before
            start = times.values[i-1]
        # fix the dumb way numpy uses datetime /timestamp objects
        start = pd.Timestamp(start).tz_localize("UTC")
        #filter in between start and current time
        filtered_current = current_df.loc[start:time]["_value"]

        currents.append(np.mean(filtered_current))
    return  currents

def filter_shutters(data, shutters):
    """
    filter all shutter query info for beamline shutters and current

    Args:
        data (dict): diamon data
        shutters (dict): shutter df

    Returns:
        dict: diamon data with out data having a current and shutter status at each timestep
    """
    #get beamline and building names for data being measured
    building, shutter = get_names(data["reference"])
    # if on the epb no shutter info - not near a beamline only get current
    if shutter != "epb" and building == "ts2":
        sel_shutter = shutters[shutter].set_index(["_time"])
        data["out"]["shutter-open"] = [get_query_info(sel_shutter, time) for time in data["out"]["datetime"]]
    #call function to extract ts1 and ts2 current
    ts1 = shutters["ts1_current"].set_index(["_time"])
    ts2 = shutters["ts2_current"].set_index(["_time"])
    data["out"]["ts1_current"] = get_current_info(data, ts1)
    data["out"]["ts2_current"] = get_current_info(data, ts2)
    data["out"]["ts1_current"] = data["out"]["ts1_current"].fillna(0)
    data["out"]["ts2_current"] = data["out"]["ts2_current"].fillna(0)
    
    #normalise dose to the current
    data = normalise_dose(data)
    return data

# TODO: fix dose when 0 current 
def normalise_dose(data):
    """
    normalise dose measurement to the current
    Args:
        data (dict): dict of measurement data

    Returns:
        dict: data with extra col for normalised dose
    """
    target_station = get_names(data["reference"])[0]
    if target_station == "ts1":
        #divide by mean current at the time and for 0 current set dose to 0
        data["out"]["norm_dose"] = data["out"]["H*(10)r"].divide(data["out"]["ts1_current"]).replace(np.inf, 0)
    if target_station == "ts2":
        data["out"]["norm_dose"] = data["out"]["H*(10)r"].divide(data["out"]["ts2_current"]).replace(np.inf, 0)
    return data

def dominant_energy(energy):
    """
    find dominant energy 
    Args:
        energy (array): 3 energy values for thermal, epithermal and fast neutrons

    Returns:
        float: value at highest %
    """
    dominant = max(energy, key=energy.get)
    return dominant

def find_significant(energy, energy_type):
    """
    get dominant energy and only if is bigger than 50% of all neutrons
    Args:
        energy (array): _description_
        energy_type (str): thermal, epi or fast

    Returns:
        float:  max energy
    """
    if max(energy, key=energy.get) == energy_type and max(energy.values()) > 0.5:
        return energy

def find_abs_error(dataframe):
    """
    convert % error to absolute error on value
    Args:
        dataframe (pandas df)

    Returns:
        df: abs error included in df out
    """
    for i, col in enumerate(dataframe.columns):
        if 'un%' in col:
            dataframe["abs_err " + dataframe.columns[i-1]] = dataframe[dataframe.columns[i-1]] * (dataframe[col]/100)
    return dataframe

#old function
def find_spect_peaks(data):
    """
    find the peaks for every data
    Args:
        data (list): _description_

    Returns:
        2 lists:
    """
    energy_list = []
    flux_list = []
    for spectra in data:
        energy, flux = peaks_finder(spectra)
        energy_list.append(energy)
        flux_list.append(flux)
    return energy_list, flux_list

def filter_shutter_status(data, flag):
    """
    filter the dataframe by open or closed shutter
    """
    filtered_df = []
    for result in data.values():
        #remove epb measurements with no shutter status
        if "shutter-open" in result["out"].keys():
            filtered_df = filtered_df + (last_row_shutter_change(result))
    df = pd.DataFrame(filtered_df)
    return flag_shutter(df, flag)

def last_row_shutter_change(result):
    """
    goes through shutter df and look for time of last change
    Args:
        result (dict): dictionary of result data

    Returns:
        list: list of shutter status
    """
    data = result["out"]
    data = data[result["out"]["t(s)"] > 1000]

    df = data["shutter-open"]
    #get boolean for index of row where change in status and always get last value in df
    filter = (df.ne(df.shift(-1)))
    last = df.tail(1)
    change_times = data[(filter) | (last)]
    filtered_list  = []
    for _, row in change_times.iterrows():
        dseries = convert_status_to_ds(result)
        filtered_list.append(pd.concat([dseries, row]).drop("INTERNAL"))
    return filtered_list

def flag_shutter(data, flag=False):
    """
    boolean mask of data to get data matching selected flag. flag is true/false for open/closed
    """
    return data[data["shutter-open"] == flag]
"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Diamon Analysis")
    parser.add_argument('file_name', type=argparse.FileType('r'), help="Enter the filename")
    args = parser.parse_args()
    dia.read_folder(args.file_name)"""
    