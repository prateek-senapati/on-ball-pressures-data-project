import json
import pandas as pd
import csv
import math

with open('metadata.json') as f:
    metadata = json.load(f)

tracking_data = pd.read_json('tracking_data.jsonl', lines=True)

def yard_to_meter(yard):
    return yard/1.094

def euclidean_distance(a, b):
    x = pow(a[0]-b[0], 2)
    y = pow(a[1]-b[1], 2)
    dist = math.sqrt(x+y)
    return dist

def find_player(player_id):
    for player in metadata['homePlayers']:
        if player['optaId'] == player_id:
            return player['name'], player['number']

def game_clock_minutes(game_clock_seconds):
    minutes = int(game_clock_seconds//60)
    seconds = str(int(game_clock_seconds%60)).zfill(2)
    return minutes, seconds

def on_ball_pressure(player_loc, frame):
    row = tracking_data[tracking_data['frameIdx'] == frame]
    count = 0
    for opp_player in row['awayPlayers'].iloc[0]:
        opp_player_loc = opp_player['xyz']
        if euclidean_distance(player_loc, opp_player_loc) < yard_to_meter(5):
            count += 1
    if count > 0:
        return True, count
    return False, count

def get_csv_rows(tracking_data):
    csv_rows = []
    for index, row in tracking_data.iterrows():
        frame = row['frameIdx']
        ball_loc = row['ball']['xyz']
        if (ball_loc is not None) and (row['lastTouch'] == 'home') and (row['live'] == True):
            for player in row['homePlayers']:
                player_loc = player['xyz']
                if euclidean_distance(player_loc, ball_loc) < yard_to_meter(1):
                    player_on_ball_pressure, opp_pressure_count = on_ball_pressure(player_loc, frame)
                    if player_on_ball_pressure:
                        game_clock_seconds = row['gameClock']
                        minutes, seconds = game_clock_minutes(game_clock_seconds)
                        half = row['period']
                        if half == 2:
                            minutes += 45
                        game_clock = f'{minutes}:{seconds}'
                        unix_timestamp = row['wallClock']
                        player_name, player_number = find_player(player['playerId'])
                        csv_row = [frame, game_clock, half, game_clock_seconds, unix_timestamp, player_number, player_name,
                                   player_loc, ball_loc, opp_pressure_count]
                        csv_rows.append(csv_row)
    return csv_rows

with open('on_ball_pressures.csv', 'w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Frame Index', 'Game Clock Time (min:sec)', 'Half', 'Game Clock (in seconds since start of half)',
                         'Unix Timestamp', 'On-ball Player Number', 'On-ball Player Name', 'On-ball Player Coordinates',
                         'Ball Coordinates', 'Number of Opposition Players within 5 yd'])
    csv_rows = get_csv_rows(tracking_data)
    csv_writer.writerows(csv_rows)
