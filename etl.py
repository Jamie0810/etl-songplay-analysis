import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *
import json


def process_song_file(cur, filepath):
    # open song file
    with open(filepath) as json_file:
        data = json.load(json_file)
    df = pd.DataFrame(data, index=[0])

    # insert song record
    song_df = df[['song_id', 'title', 'artist_id', 'year', 'duration']]
    song_arr = song_df.values[0]
    song_data = song_arr.tolist()
    cur.execute(song_table_insert, song_data)
    
    # insert artist record
    artist_df = df[['artist_id', 'artist_name', 'artist_location', 'artist_latitude', 'artist_longitude']]
    artist_arr = artist_df.values[0]
    artist_data = artist_arr.tolist()
    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    # open log file
    logData_arr = []
    for line in open(filepath, 'r'):
        logData_arr.append(json.loads(line))
    df = pd.DataFrame(logData_arr) 

    # Filter records by NextSong action
    df = df[df['page'].str.contains("NextSong")]

    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['ts'], unit='ms')

    # Create a list named time_data
    time_data = [df['ts'].values, df['datetime'].dt.hour.values, df['datetime'].dt.day.values, df['datetime'].dt.week.values, df['datetime'].dt.month.values, df['datetime'].dt.year.values, df['datetime'].dt.weekday.values]

    # Create time_dict
    time_dict = {}
    time_dict['start_time'] = time_data[0]
    time_dict['hour'] = time_data[1]
    time_dict['day'] = time_data[2]
    time_dict['week'] = time_data[3]
    time_dict['month'] = time_data[4]
    time_dict['year'] = time_data[5]
    time_dict['weekday'] = time_data[6]

    # Convert time_dict into time_df
    time_df = pd.DataFrame.from_dict(time_dict)

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId', 'firstName', 'lastName', 'gender', 'level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        # get songid and artistid from song and artist tables
        cur.execute(song_select)
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = (row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()