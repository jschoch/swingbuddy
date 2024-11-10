# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

#  doing stuff
import os
import datetime
import sys
import glob
from peewee import *
from swingdb import Swing, Session,Config
import requests
from io import StringIO
import pandas as pd

testdb = SqliteDatabase('test.db')

def get_files_with_extension(directory, extension):
    return [os.path.join(directory, f) for f in os.listdir(directory) if
            (os.path.isfile(os.path.join(directory, f)) and
             os.path.splitext(f)[1].lower() == f'.{extension.lower()}' and
             os.path.getsize(os.path.join(directory, f)) > 0)]


def sort_by_creation_time(files):
    sorted_files = sorted(files, key=lambda x: os.path.getctime(x))
    return sorted_files


def find_swing(directory_path,extension):
    print(f"finding swing videos from {directory_path}")
    # how do i use logger from here?

    print(f"directory path {directory_path}")
    #extension = 'trc'  # Change this to your desired extension
    files = get_files_with_extension(directory_path, extension)
    #print(f" files: {files}")
    sorted_files = sort_by_creation_time(files)
    if(len(sorted_files) > 0):
        print(sorted_files[-2:])
        return(sorted_files[-2:])

    #return vid

def get_pairs(directory_path):
    file_pairs = {}
    files = os.listdir(directory_path)

    for file_name in files:
        # Extract the prefix (everything before the second underscore)
        parts = file_name.split('-')
        if len(parts) < 3:  # Ensure there is a second hyphen
            continue

        prefix = '-'.join(parts[:2])

        if prefix not in file_pairs:
            file_pairs[prefix] = []

        file_pairs[prefix].append(file_name)

    # Filter out pairs with only one file
    file_pairs = {prefix: files for prefix, files in file_pairs.items() if len(files) > 1}

    #print(file_pairs.keys())
    return file_pairs

def gen_trc():
    print('gen trc')

def gen_screenshot():
    print('gen screen')
    # spin up thread and timer to grab the screenshot

def proc_screenshot(fname):
    print(f"processing screenshot: {fname}")

def ocr_screen():
    print('ocr')

def testdb():
    print("setting up test db")
    db.drop_tables([Swing,Config,Session])
    db.create_tables([Swing,Config,Session])
    Config.get_or_create(id=1, vidDir="./test_data/swings")
    return db

def fetch_trc(config,swing,logger):
    #url = config.poseServer + "?path="+ requests.utils.quote(swing.rightVid)
    url = config.poseServer + "?path="+ requests.utils.quote(swing.dtlVid)
    logger.debug(f" url: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        #logger.debug(f"woot, got trc\n{response.text} encoding: {response.encoding}")
        logger.debug(f"woot, got trc encoding: {response.encoding}")
        return response.text
    else:
        return "ERROR"

def test_fetch_trc(config):

    url = config.poseServer + "?path="+ requests.utils.quote('c:/Files/test_small.mp4')
    print(f" url: {url}")
    contents = requests.get(url)
    return contents

def fFUCKYOU():
    s = ",x,y,z,X1,Y1,Distance,Speed,Distance_filtered,Speed_filtered\n0,0.47143858221602364,-0.6957345381271879,0.0,471.43858221602363,695.7345381271879,5.412010562840744,3.846183380369675,5.329372161704745,3.78745429229068\n1,0.4764572394563091,-0.6937089671368668,0.0,476.4572394563091,693.7089671368668,5.412010562840744,3.846183380369675,4.444640207832074,3.1586969575524217\n2,0.48021433891631476,-0.6922061293837571,0.0,480.2143389163148,692.2061293837571,4.046519203531211,2.8757621087862733,3.458046823287001,2.4575491983676834\n3,0.4820892152510594,-0.6914728571898271,0.0,482.0892152510594,691.4728571898271,2.0131689896718403,1.4307099034720219,2.477441679366929,1.760657135158054\n4,0.48222415379244943,-0.6914871861409991,0.0,482.22415379244944,691.4871861409991,0.13569719523323556,0.09643667376637527,1.615811546450894,1.1483176988676946\n5,0.48133166424576707,-0.6920147373068408,0.0,481.33166424576706,692.0147373068409,1.0367486790530671,0.7367918988134946,0.9654154716291102,0.6860971350696482\n6,0.4802403836077247,-0.6927051735876167,0.0,480.2403836077247,692.7051735876167,1.2913542073256865,0.9177338131024388,0.5780048639543801,0.41077390291479976\n7,0.47947133057939945,-0.6932510946248605,0.0,479.4713305793994,693.2510946248605,0.9431184121209547,0.6702511608765676,0.45673771606797386,0.32459231044193737\n8,0.4792270839462855,-0.6934408007358596,0.0,479.2270839462855,693.4408007358595,0.3092649775481588,0.2197870464154768,0.5604493013348946,0.3982975944530624\n9,0.47953338753920705,-0.6931646029929677,0.0,479.53338753920707,693.1646029929676,0.4124404008038363,0.29311129321448864,0.8169899708078509,0.5806147662063003\n10,0.4803473511279972,-0.6924408537746491,0.0,480.34735112799723,692.4408537746491,1.089196793464257,0.7740654894020099,1.1409520652550116,0.8108466937061591\n11,0.4816485491084868,-0.6914317042027817,0.0,481.6485491084868,691.4317042027817,1.6466630022048534,1.1702430729968087,1.4515406730747793,1.0315744117432672\n12,0.4833632139715679,-0.69045798017487,0.0,483.3632139715679,690.45798017487,1.9718554904499135,1.4013494112395595,1.6871690155847336,1.1990297048146403\n13,0.48523305025560665,-0.6898871880097731,0.0,485.23305025560666,689.8871880097731,1.955016988377296,1.3893827001494712,1.8141459683946994,1.2892691158277907\n14,0.486927700016549,-0.6899127716032338,0.0,486.927700016549,689.9127716032339,1.694842863665049,1.2044833207319223,1.8280737547058676,1.2991672525023896\n15,0.4882910155680351,-0.6904836172069598,0.0,488.2910155680351,690.4836172069598,1.4780033816663243,1.0503808107335497,1.7485396290589796,1.2426442969975278\n16,0.48937170900921245,-0.6914177416161568,0.0,489.37170900921245,691.4177416161567,1.4284560636089532,1.0151687450804252,1.6096865806114455,1.1439648356307237\n17,0.49020218143690497,-0.6925696638271894,0.0,490.202181436905,692.5696638271894,1.4200736718311378,1.009211584507801,1.450158761659178,1.0305923211397716\n"
    sio = StringIO(s)
    df = pd.read_csv(sio)
    print(f"df info: {df.info()}")
