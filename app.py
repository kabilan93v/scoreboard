from flask import Flask, render_template, request, redirect, url_for
import qrcode
import os

app = Flask(__name__)
app.secret_key = 'cricket-score-key'

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

def generate_qr():
    public_url = "https://scoreboard-wxtx.onrender.com/viewer"
    output_path = os.path.join('static', 'qr.png')
    img = qrcode.make(public_url)
    img.save(output_path)

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
    state = match_state
    batter1 = state['score']['batter1']
    batter2 = state['score']['batter2']
    striker = state['striker']
    bowler = state['bowlers'].get(state['current_bowler'], {'name': '', 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0})
    max_balls = state['total_overs'] * 6
    over_display = f"{state['balls'] // 6}.{state['balls'] % 6}"
    crr = round((state['runs'] / ((state['balls'] - state['extras']) / 6)) if state['balls'] - state['extras'] > 0 else 0, 2)
    match_over = state['balls'] >= max_balls
    target_runs = state['team1_score'] if state['first_innings_over'] else None
    runs_needed = target_runs - state['runs'] + 1 if target_runs else None

    if state['first_innings_over'] and state['runs'] > target_runs:
        match_over = True

    if request.method == 'POST':
        form = request.form
        if 'batter1_name' in form:
            batter1['name'] = form['batter1_name']
            batter2['name'] = form['batter2_name']
        elif 'new_batter' in form:
            state['score'][striker] = {'name': form['new_batter'], 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
            state['awaiting_new_batter'] = False
        elif 'new_bowler' in form:
            new_bowler = form['new_bowler']
            state['current_bowler'] = new_bowler
            if new_bowler not in state['bowlers']:
                state['bowlers'][new_bowler] = {'name': new_bowler, 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0}
            state['awaiting_new_bowler'] = False
        elif 'event' in form:
            event = form['event']
            if event.isdigit():
                runs = int(event)
                state['runs'] += runs
                state['balls'] += 1
                batter = state['score'][striker]
                batter['runs'] += runs
                batter['balls'] += 1
                if runs == 4: batter['fours'] += 1
                if runs == 6: batter['sixes'] += 1
                if runs % 2 == 1:
                    state['striker'] = 'batter2' if striker == 'batter1' else 'batter1'
                bowler['runs'] += runs
                bowler['balls'] += 1
                state['recent_overs'].append(event)
            elif event == 'W':
                state['wickets'] += 1
                state['balls'] += 1
                state['score'][striker]['balls'] += 1
                bowler['wickets'] += 1
                bowler['balls'] += 1
                state['awaiting_new_batter'] = True
                state['recent_overs'].append('W')
            elif event in ['WD', 'NB']:
                state['runs'] += 1
                state['extras'] += 1
                bowler['runs'] += 1
                if event == 'WD': bowler['wd'] += 1
                if event == 'NB': bowler['nb'] += 1
                state['recent_overs'].append(event.lower())

            if bowler['balls'] > 0 and bowler['balls'] % 6 == 0:
                state['awaiting_new_bowler'] = True
            state['bowlers'][state['current_bowler']] = bowler

        elif 'end_innings' in form:
            state['team1_score'] = state['runs']
            state['first_innings_over'] = True
            state['batting_team'] = state['team2']
            state['runs'] = 0
            state['wickets'] = 0
            state['balls'] = 0
            state['extras'] = 0
            state['recent_overs'] = []
            state['score'] = {
                'batter1': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
                'batter2': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
            }
            state['bowlers'] = {}
            state['current_bowler'] = ''
            state['striker'] = 'batter1'
            state['awaiting_new_batter'] = False
            state['awaiting_new_bowler'] = True

        return redirect(url_for('scoreboard'))

    result = ''
    if state['first_innings_over'] and match_over:
        team2_score = state['runs']
        team1_score = state['team1_score']
        if team2_score > team1_score:
            result = f"{state['team2']} won by {10 - state['wickets']} wickets"
        elif team2_score < team1_score:
            result = f"{state['team1']} won by {team1_score - team2_score} runs"
        else:
            result = "Match Tied!"

    return render_template('scoreboard.html', **state,
        batter1=batter1, batter2=batter2, bowler=bowler, striker=striker,
        over_display=over_display, crr=crr, match_over=match_over,
        target_runs=target_runs, runs_needed=runs_needed,
        show_result=bool(result), result=result,
        show_batter_name_form=not batter1['name'] or not batter2['name'],
        show_bowler_name_form=state['awaiting_new_bowler'],
        show_run_buttons=not state['awaiting_new_bowler'] and not state['awaiting_new_batter'],
        show_end_innings=not state['first_innings_over'] and match_over
    )

@app.route('/viewer')
def viewer():
    state = match_state
    batter1 = state['score']['batter1']
    batter2 = state['score']['batter2']
    striker = state['striker']
    bowler = state['bowlers'].get(state['current_bowler'], {'name': '', 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0})
    over_display = f"{state['balls'] // 6}.{state['balls'] % 6}"
    crr = round((state['runs'] / ((state['balls'] - state['extras']) / 6)) if state['balls'] - state['extras'] > 0 else 0, 2)
    match_over = state['balls'] >= state['total_overs'] * 6
    target_runs = state['team1_score'] if state['first_innings_over'] else None
    runs_needed = target_runs - state['runs'] + 1 if target_runs else None

    result = ''
    if state['first_innings_over'] and match_over:
        if state['runs'] > state['team1_score']:
            result = f"{state['team2']} won by {10 - state['wickets']} wickets"
        elif state['runs'] < state['team1_score']:
            result = f"{state['team1']} won by {state['team1_score'] - state['runs']} runs"
        else:
            result = "Match Tied!"

    return render_template("viewer.html", **state,
        batter1=batter1, batter2=batter2, bowler=bowler, striker=striker,
        over_display=over_display, crr=crr, match_over=match_over,
        show_result=bool(result), result=result,
        target_runs=target_runs, runs_needed=runs_needed
    )

if __name__ == '__main__':
    app.run(debug=True)
