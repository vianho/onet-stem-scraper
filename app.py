import logging
import requests
from requests.api import request
import constants as c
from itertools import combinations
import pandas as pd
from os.path import exists
from bs4 import BeautifulSoup
import time

LOGGER = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    datefmt='%d-%b-%y %H:%M:%S', 
    handlers=[
        logging.FileHandler(c.LOGFILE_PATH, 'a', 'utf-8'),
        logging.StreamHandler()
    ]
)

url_2 = "https://www.onetonline.org/explore/interests-table/{}/{}/{}_{}.csv?fmt=csv"
url_3 = "https://www.onetonline.org/explore/interests-table/{}/{}/{}/{}_{}_{}.csv?fmt=csv"

url_occ = "https://www.onetonline.org/link/details/{}"

def get_riasec_combination(riasec):
    """
    Get the combination of 3 riasec codes and job zone
    @return: [[rc1, rc2, rc3], [rc1, rc2], ...]
    """
    riasec_combi = list(combinations(riasec, 3))
    riasec_combi += list(combinations(riasec, 2))
    return riasec_combi

def filter_zone(csv, min_zone):
    """
    Filter the csv file by zone
    @param csv: csv file
    @param min_zone: min_zone
    @return: filtered csv file
    """
    df = pd.read_csv(csv)
    LOGGER.info(f'number of rows before filtering = {len(df)}')
    filtered_df = df.loc[df['Job Zone'] >= min_zone]
    LOGGER.info(f'Number of rows after filtering = {len(filtered_df)}')
    return filtered_df

def remove_duplicates(all_occupation_file):
    """
    Remove duplicates from all_occupation_file
    @param all_occupation_file: all_occupation_file
    """
    df = pd.read_csv(all_occupation_file)
    df.drop_duplicates(subset=['Code'], keep='first', inplace=True)
    df.to_csv(c.ALL_OCCUPATION_FILE, index=False)

def merge_stem_occupation(all_occupation_file, stem_occupation_file):
    """
    Merge the stem_occupation_file with all_occupation_file
    @param all_occupation_file: all_occupation_file
    @param stem_occupation_file: stem_occupation_file
    @return: merged dataframe
    """
    all_df = pd.read_csv(all_occupation_file)
    stem_df = pd.read_csv(stem_occupation_file)
    merged_df = pd.merge(stem_df, all_df, on='Code', how='left')
    merged_df = merged_df.drop(columns=['Occupation_y'])
    merged_df.columns = ['Occupation' if x=='Occupation_x' else x for x in merged_df.columns]
    LOGGER.info(f'merged_df.count() = \n{merged_df.count()}')
    return merged_df

def get_stem_occupation_job_titles(stem_occupation_file):
    """
    Get the job titles of stem_occupation_file
    @param stem_occupation_file: stem_occupation_file
    @return: job titles
    """
    df = pd.read_csv(stem_occupation_file)
    job_titles = []
    occ_code = df['Code'].to_list()
    LOGGER.info(f'number of occ_code = {len(occ_code)}')
    for i, code in enumerate(occ_code):
        if i % 10 == 0:
            time.sleep(5)
        url = url_occ.format(code)
        r = requests.get(url)
        try:
            job_title = BeautifulSoup(r.text, 'html.parser').select_one('#content > p:nth-child(5)').text.strip().split('\n')[-1]
            LOGGER.info(f'{job_title=}')
        except:
            job_title = ''
        job_titles.append(job_title)
    job_titles = pd.Series(job_titles)
    job_titles.name = 'Job Titles'
    df = pd.concat([df, job_titles], axis=1)
    LOGGER.info(f'df.count() = \n{df.count()}')
    df.to_csv(c.STEM_OCCUPATION_JOB_TITLE_FILE, index=False)
    return df

    


def main():
    riasec_zone_combi = get_riasec_combination(c.RIASEC_CODES)
    LOGGER.info(f'number of combinations = {len(riasec_zone_combi)}')

    file_exists = exists(c.ALL_OCCUPATION_FILE)
    if not file_exists:
        # create dataset
        for i, rz in enumerate(riasec_zone_combi):
            print(f'{rz=}')
            url = url_3.format(rz[0], rz[1], rz[2], rz[0], rz[1], rz[2]) if len(rz) == 3 else url_2.format(rz[0], rz[1], rz[0], rz[1])
            LOGGER.info(f'url = {url}')
            r = requests.get(url)

            with open(c.ALL_OCCUPATION_FILE, 'a') as f:
                text = ''
                if i == 0:
                    text += 'Code,Occupation,Job Zone,Interest1,Interest2,Interest3\n'
                text += '\n'.join(r.text.split('\n')[1:])
                f.write(text)
    
    # remove duplicates
    remove_duplicates(c.ALL_OCCUPATION_FILE)

    # filter occupations based on job zone
    # filtered_by_zone = filter_zone(c.ALL_OCCUPATION_FILE, c.MIN_ZONE)
    # filtered_by_zone.to_csv(c.FILTERED_OCCUPATION_BY_ZONE_FILE, index=False)

    #  get stem occupations job titles
    get_stem_occupation_job_titles(c.STEM_OCCUPATION_FILE)

    # merge all_occupation_file with stem_occupation_file
    merged_df = merge_stem_occupation(c.ALL_OCCUPATION_FILE, c.STEM_OCCUPATION_JOB_TITLE_FILE)
    merged_df.to_csv(c.MERGED_OCCUPATION_FILE, index=False)


if __name__ == '__main__':
    main()

