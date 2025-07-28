from flask import Flask, render_template, request, redirect, url_for
import qrcode
import os

app = Flask(__name__)
app.secret_key = 'cricket-score-key'

# Global match state
match_state = {
    'team1': '', 'team2': '', 'total_overs': 0,
    'batting_team': '', 'runs': 0, 'wickets': 0, 'balls': 0, 'extras': 0,
    'recent_overs': [],
    'score': {
        'batter1': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
        'batter2': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
    },
    'bowlers': {}, 'current_bowler': '', 'striker': 'batter1',
    'awaiting_new_batter': False, 'awaiting_new_bowler': True,
    'first_innings_over': False, 'team1_score': 0
}

# Generate QR code once
def generate_qr():
    url = "https://scoreboard-wxtx.onrender.com/viewer"
    output = os.path.join('static', 'qr.png')
    if not os.path.exists(output):
        img = qrcode.make(url)
        img.save(output)

generate_qr()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        match_state.update({
            'team1': request.form['team1'],
            'team2': request.form['team2'],
            'total_overs': int(request.form['total_overs']),
            'batting_team': request.form['team1'],
            'runs': 0, 'wickets': 0, 'balls': 0, 'extras': 0,
            'recent_overs': [],
            'score': {
                'batter1': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
                'batter2': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
            },
            'bowlers': {}, 'current_bowler': '', 'striker': 'batter1',
            'awaiting_new_batter': False, 'awaiting_new_bowler': True,
            'first_innings_over': False, 'team1_score': 0
        })
        return redirect(url_for('scoreboard'))
    return render_template('index.html')

@app.route('/scoreboard', methods=['GET', 'POST'])
def scoreboard():
    s = match_state
    batter1 = s['score']['batter1']
    batter2 = s['score']['batter2']
    striker = s['striker']
    bowler = s['bowlers'].get(s['current_bowler'], {'name': '', 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0})
    over_display = f"{s['balls'] // 6}.{s['balls'] % 6}"
    crr = round((s['runs'] / ((s['balls'] - s['extras']) / 6)) if s['balls'] - s['extras'] > 0 else 0, 2)
    match_over = s['balls'] >= s['total_overs'] * 6
    target_runs = s['team1_score'] if s['first_innings_over'] else None
    runs_needed = (target_runs - s['runs'] + 1) if target_runs else None

    if s['first_innings_over'] and s['runs'] > target_runs:
        match_over = True

    if request.method == 'POST':
        f = request.form
        if 'batter1_name' in f:
            batter1['name'] = f['batter1_name']
            batter2['name'] = f['batter2_name']
        elif 'new_batter' in f:
            s['score'][striker] = {'name': f['new_batter'], 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
            s['awaiting_new_batter'] = False
        elif 'new_bowler' in f:
            s['current_bowler'] = f['new_bowler']
            if f['new_bowler'] not in s['bowlers']:
                s['bowlers'][f['new_bowler']] = {'name': f['new_bowler'], 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0}
            s['awaiting_new_bowler'] = False
        elif 'event' in f:
            event = f['event']
            if event.isdigit():
                r = int(event)
                s['runs'] += r
                s['balls'] += 1
                b = s['score'][striker]
                b['runs'] += r
                b['balls'] += 1
                if r == 4: b['fours'] += 1
                if r == 6: b['sixes'] += 1
                if r % 2 == 1:
                    s['striker'] = 'batter2' if striker == 'batter1' else 'batter1'
                bowler['runs'] += r
                bowler['balls'] += 1
                s['recent_overs'].append(event)
            elif event == 'W':
                s['wickets'] += 1
                s['balls'] += 1
                s['score'][striker]['balls'] += 1
                bowler['wickets'] += 1
                bowler['balls'] += 1
                s['awaiting_new_batter'] = True
                s['recent_overs'].append('W')
            elif event in ['WD', 'NB']:
                s['runs'] += 1
                s['extras'] += 1
                bowler['runs'] += 1
                if event == 'WD': bowler['wd'] += 1
                if event == 'NB': bowler['nb'] += 1
                s['recent_overs'].append(event.lower())

            if bowler['balls'] > 0 and bowler['balls'] % 6 == 0:
                s['awaiting_new_bowler'] = True
            s['bowlers'][s['current_bowler']] = bowler

        elif 'end_innings' in f:
            s['team1_score'] = s['runs']
            s['first_innings_over'] = True
            s['batting_team'] = s['team2']
            s['runs'] = s['wickets'] = s['balls'] = s['extras'] = 0
            s['recent_overs'] = []
            s['score'] = {
                'batter1': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
                'batter2': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
            }
            s['bowlers'] = {}
            s['current_bowler'] = ''
            s['striker'] = 'batter1'
            s['awaiting_new_batter'] = False
            s['awaiting_new_bowler'] = True

        return redirect(url_for('scoreboard'))

    result = ""
    if s['first_innings_over'] and match_over:
        if s['runs'] > s['team1_score']:
            result = f"{s['team2']} won by {10 - s['wickets']} wickets"
        elif s['runs'] < s['team1_score']:
            result = f"{s['team1']} won by {s['team1_score'] - s['runs']} runs"
        else:
            result = "Match Tied!"

    return render_template("scoreboard.html",
        batter1=batter1, batter2=batter2, bowler=bowler, striker=striker,
        runs=s['runs'], wickets=s['wickets'], balls=s['balls'], extras=s['extras'],
        over_display=over_display, crr=crr, recent_overs=s['recent_overs'][-6:],
        match_over=match_over, show_result=bool(result), result=result,
        show_batter_name_form=not batter1['name'] or not batter2['name'],
        show_bowler_name_form=s['awaiting_new_bowler'],
        show_run_buttons=not s['awaiting_new_bowler'] and not s['awaiting_new_batter'],
        show_end_innings=not s['first_innings_over'] and match_over,
        awaiting_new_batter=s['awaiting_new_batter'],
        target_runs=target_runs, runs_needed=runs_needed,
        batting_team=s['batting_team'],
        team1=s['team1'], team2=s['team2']
    )

@app.route("/viewer")
def viewer():
    s = match_state
    batter1 = s['score']['batter1']
    batter2 = s['score']['batter2']
    striker = s['striker']
    bowler = s['bowlers'].get(s['current_bowler'], {'name': '', 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0})
    over_display = f"{s['balls'] // 6}.{s['balls'] % 6}"
    crr = round((s['runs'] / ((s['balls'] - s['extras']) / 6)) if s['balls'] - s['extras'] > 0 else 0, 2)
    match_over = s['balls'] >= s['total_overs'] * 6
    result = ""
    if s['first_innings_over'] and match_over:
        if s['runs'] > s['team1_score']:
            result = f"{s['team2']} won by {10 - s['wickets']} wickets"
        elif s['runs'] < s['team1_score']:
            result = f"{s['team1']} won by {s['team1_score'] - s['runs']} runs"
        else:
            result = "Match Tied!"

    return render_template("viewer.html",
        batter1=batter1, batter2=batter2, bowler=bowler, striker=striker,
        runs=s['runs'], wickets=s['wickets'], balls=s['balls'], extras=s['extras'],
        over_display=over_display, crr=crr, recent_overs=s['recent_overs'][-6:],
        match_over=match_over, show_result=bool(result), result=result,
        target_runs=s['team1_score'] if s['first_innings_over'] else None,
        runs_needed=(s['team1_score'] - s['runs'] + 1) if s['first_innings_over'] else None,
        team1=s['team1'], team2=s['team2'], batting_team=s['batting_team'],
        match_state=s,show_result=bool(result), result=result)
    

if __name__ == '__main__':
    app.run(debug=True)
