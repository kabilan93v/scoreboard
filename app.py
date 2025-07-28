from flask import Flask, render_template, request, redirect, url_for, session
import qrcode
import os

app = Flask(__name__)
app.secret_key = 'cricket-score-key'


def generate_qr():
    public_url = "https://scoreboard-wxtx.onrender.com/viewer"
    output_path = os.path.join('static', 'qr.png')
    if not os.path.exists(output_path):
        img = qrcode.make(public_url)
        img.save(output_path)


generate_qr()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['team1'] = request.form['team1']
        session['team2'] = request.form['team2']
        session['total_overs'] = int(request.form['total_overs'])

        session['batting_team'] = session['team1']
        session['runs'] = 0
        session['wickets'] = 0
        session['balls'] = 0
        session['extras'] = 0
        session['recent_overs'] = []
        session['score'] = {
            'batter1': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
            'batter2': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
        }
        session['bowlers'] = {}
        session['current_bowler'] = ''
        session['striker'] = 'batter1'
        session['awaiting_new_batter'] = False
        session['awaiting_new_bowler'] = True
        session['first_innings_over'] = False
        session['team1_score'] = 0
        return redirect(url_for('scoreboard'))
    return render_template('index.html')

@app.route('/scoreboard', methods=['GET', 'POST'])
def scoreboard():
    score = session['score']
    striker = session['striker']
    batter1 = score['batter1']
    batter2 = score['batter2']
    current_bowler = session.get('current_bowler', '')
    bowler = session['bowlers'].get(current_bowler, {'name': '', 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0})
    total_overs = session.get('total_overs', 0)
    max_balls = total_overs * 6
    total_balls = session['balls']
    completed_overs = total_balls // 6
    balls_in_current_over = total_balls % 6
    over_display = f"{completed_overs}.{balls_in_current_over}"
    crr = round((session['runs'] / ((session['balls'] - session['extras']) / 6)) if session['balls'] - session['extras'] > 0 else 0, 2)
    target_runs = None
    runs_needed = None
    if session.get('first_innings_over'):
        target_runs = session.get('team1_score', 0)
        runs_needed = target_runs - session['runs'] + 1

    match_over = session['balls'] >= max_balls
    match_over = session['balls'] >= max_balls
    if session.get('first_innings_over'):
        team1_score = session.get('team1_score', 0)
        if session['runs'] > team1_score:
            match_over = True


    show_batter_name_form = (not batter1['name'] or not batter2['name']) and session['balls'] == 0
    show_bowler_name_form = session.get('awaiting_new_bowler', False) and not match_over
    show_run_buttons = not match_over and not session.get('awaiting_new_bowler') and not session.get('awaiting_new_batter')

    
    if request.method == 'POST':
        if 'batter1_name' in request.form and 'batter2_name' in request.form:
            score['batter1']['name'] = request.form['batter1_name']
            score['batter2']['name'] = request.form['batter2_name']
            session.modified = True
            return redirect(url_for('scoreboard'))

        elif 'new_batter' in request.form:
            new_name = request.form.get('new_batter')
            if new_name:
                out_batter = striker
                score[out_batter] = {'name': new_name, 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
                session['awaiting_new_batter'] = False
                session.modified = True
                return redirect(url_for('scoreboard'))

        elif 'new_bowler' in request.form:
            new_bowler = request.form.get('new_bowler')
            if new_bowler:
                session['current_bowler'] = new_bowler
                if new_bowler not in session['bowlers']:
                    session['bowlers'][new_bowler] = {'name': new_bowler, 'balls': 0, 'runs': 0, 'wickets': 0, 'nb': 0, 'wd': 0}
                session['awaiting_new_bowler'] = False
                session.modified = True
                return redirect(url_for('scoreboard'))

        elif 'event' in request.form and show_run_buttons:
            event = request.form['event']
            if event.isdigit():
                runs = int(event)
                session['runs'] += runs
                session['balls'] += 1
                score[striker]['runs'] += runs
                score[striker]['balls'] += 1
                if runs == 4:
                    score[striker]['fours'] += 1
                elif runs == 6:
                    score[striker]['sixes'] += 1
                if runs % 2 == 1:
                    session['striker'] = 'batter2' if striker == 'batter1' else 'batter1'
                bowler['runs'] += runs
                bowler['balls'] += 1
                session['recent_overs'].append(event)

            elif event == 'W':
                session['wickets'] += 1
                session['balls'] += 1
                score[striker]['balls'] += 1
                bowler['wickets'] += 1
                bowler['balls'] += 1
                session['awaiting_new_batter'] = True
                session['recent_overs'].append('W')

            elif event == 'WD':
                session['runs'] += 1
                session['extras'] += 1
                bowler['runs'] += 1
                bowler['wd'] += 1
                session['recent_overs'].append('wd')

            elif event == 'NB':
                session['runs'] += 1
                session['extras'] += 1
                bowler['runs'] += 1
                bowler['nb'] += 1
                session['recent_overs'].append('nb')

            if bowler['balls'] > 0 and bowler['balls'] % 6 == 0:
                session['awaiting_new_bowler'] = True

            session['bowlers'][current_bowler] = bowler
            session.modified = True
            return redirect(url_for('scoreboard'))

        elif 'end_innings' in request.form:
            
            session['team1_score'] = session['runs']
            session['team1_wickets'] = session['wickets']
            session['team1_overs'] = over_display
            session['first_innings_over'] = True


            session['batting_team'] = session['team2']
            session['runs'] = 0
            session['wickets'] = 0
            session['balls'] = 0
            session['extras'] = 0
            session['recent_overs'] = []
            session['score'] = {
                'batter1': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
                'batter2': {'name': '', 'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0},
            }
            session['bowlers'] = {}
            session['current_bowler'] = ''
            session['striker'] = 'batter1'
            session['awaiting_new_batter'] = False
            session['awaiting_new_bowler'] = True
            return redirect(url_for('scoreboard'))


    if session.get('first_innings_over') and match_over:
        team1_score = session.get('team1_score', 0)
        team2_score = session['runs']
        if team2_score > team1_score:
            result = f"{session['team2']} won by {10 - session['wickets']} wickets"
        elif team2_score < team1_score:
            result = f"{session['team1']} won by {team1_score - team2_score} runs"
        else:
            result = "Match Tied!"
        return render_template('scoreboard.html',
                               batter1=batter1, batter2=batter2, bowler=bowler,
                               striker=striker, runs=session['runs'], match_over=True,
                               wickets=session['wickets'], balls=session['balls'],
                               extras=session['extras'], over_display=over_display,
                               crr=crr, recent_overs=session['recent_overs'][-6:],
                               show_result=True, result=result,awaiting_new_batter=session.get('awaiting_new_batter', False),target_runs=target_runs,
runs_needed=runs_needed
)

    return render_template('scoreboard.html',
                           batter1=batter1, batter2=batter2, bowler=bowler,
                           striker=striker, runs=session['runs'], match_over=match_over,
                           wickets=session['wickets'], balls=session['balls'],
                           extras=session['extras'], over_display=over_display,
                           crr=crr, recent_overs=session['recent_overs'][-6:],
                           show_batter_name_form=show_batter_name_form,
                           show_bowler_name_form=show_bowler_name_form,
                           show_run_buttons=show_run_buttons,
                           show_end_innings=not session.get('first_innings_over') and match_over,awaiting_new_batter=session.get('awaiting_new_batter', False),target_runs=target_runs,
runs_needed=runs_needed
)
@app.route("/viewer")
def viewer():
    return render_template("viewer.html")


