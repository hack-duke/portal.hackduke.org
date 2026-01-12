import os
from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from datetime import datetime
from db import (
    get_local_session,
    init_db,
    resolve_name,
    get_all_check_ins,
    get_check_in,
    create_check_in,
    delete_check_in,
    search_check_ins
)

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize database tables
init_db()


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/log_user', methods=['POST'])
def log_user():
    db = get_local_session()
    try:
        data = request.json
        if not data or 'qrCode' not in data or 'eventType' not in data:
            socketio.emit('notification', {
                'success': False,
                'message': 'Invalid request'
            })
            return jsonify({'error': 'Invalid request'}), 400

        user_id = data['qrCode']
        event_type = data['eventType']

        # Resolve user name from database
        name = resolve_name(db, user_id)
        if not name:
            socketio.emit('notification', {
                'success': False,
                'message': 'User not found in DB'
            })
            return jsonify({'error': 'User not found in DB'}), 400

        # Check if user has already checked in for this event type
        existing_check_in = get_check_in(db, user_id, event_type)
        if existing_check_in:
            check_in_time = existing_check_in.check_in_time.strftime('%H:%M')
            socketio.emit('notification', {
                'success': False,
                'message': f'{name} already checked in at {check_in_time}'
            })
            return jsonify({'error': f'{name} already checked in: {event_type}'}), 400

        # Create new check-in
        create_check_in(db, user_id, name, event_type)

        # Get updated log and broadcast
        user_log = get_all_check_ins(db)
        socketio.emit('update_log', {
            'log': user_log,
            'total_users': len(user_log)
        })
        socketio.emit('notification', {
            'success': True,
            'message': 'Check-in successful'
        })
        return jsonify({'message': 'User logged successfully'}), 200

    except Exception as e:
        socketio.emit('notification', {
            'success': False,
            'message': f'Error: {str(e)}'
        })
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/log', methods=['GET'])
def display_log():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>User Log</title>
        <link href="https://fonts.googleapis.com/css2?family=Oxygen:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Oxygen', sans-serif;
                background-color: #1d42c6;
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
                text-align: center;
            }

            h1 {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }

            p {
                font-size: 1.2rem;
            }

            #log {
                margin-top: 1rem;
            }

            #search-bar {
                padding: 0.5rem;
                width: 50%;
                border: none;
                border-radius: 5px;
                font-size: 1rem;
                margin-bottom: 1rem;
            }

            #notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
            }

            .notification {
                padding: 10px 15px;
                margin-bottom: 10px;
                border-radius: 4px;
                color: #fff;
                transition: opacity 1s;
                opacity: 1;
            }

            .success {
                background-color: #4CAF50;
            }

            .error {
                background-color: #f44336;
            }

            .fade-out {
                opacity: 0;
            }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const socket = io();
                const notificationContainer = document.createElement('div');
                notificationContainer.id = 'notification-container';
                document.body.appendChild(notificationContainer);

                socket.on('connect', () => {
                    socket.emit('request_initial_log');
                });

                socket.on('update_log', (data) => {
                    document.getElementById('total-users').textContent = data.total_users;
                    const logDiv = document.getElementById('log');
                    logDiv.innerHTML = '';
                    data.log.forEach(entry => {
                        const p = document.createElement('p');
                        p.textContent = `${entry.name} - ${entry.event_type} at ${entry.time}`;
                        const deleteButton = document.createElement('button');
                        deleteButton.textContent = 'X';
                        deleteButton.style.background = 'none';
                        deleteButton.style.color = 'red';
                        deleteButton.style.border = 'none';
                        deleteButton.style.cursor = 'pointer';
                        deleteButton.style.marginLeft = '10px';
                        deleteButton.onclick = () => {
                            fetch('/delete_log_entry', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ user_id: entry.user_id, event_type: entry.event_type })
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.message) {
                                    socket.emit('request_initial_log');
                                } else {
                                    console.error('Error deleting log entry:', data.error);
                                }
                            })
                            .catch(error => console.error('Fetch error:', error));
                        };
                        p.appendChild(deleteButton);
                        logDiv.appendChild(p);
                    });
                });

                socket.on('notification', (data) => {
                    const div = document.createElement('div');
                    div.classList.add('notification');
                    div.classList.add(data.success ? 'success' : 'error');
                    div.textContent = data.message;
                    notificationContainer.appendChild(div);

                    setTimeout(() => {
                        div.classList.add('fade-out');
                    }, 3000);
                    setTimeout(() => {
                        notificationContainer.removeChild(div);
                    }, 4000);
                });

                const searchInput = document.getElementById('search-bar');
                searchInput.addEventListener('input', () => {
                    const query = searchInput.value.trim();
                    if (query === '') {
                        socket.emit('request_initial_log');
                    } else {
                        socket.emit('search_log', { query });
                    }
                });

                socket.on('search_results', (data) => {
                    document.getElementById('total-users').textContent = data.total_users;
                    const logDiv = document.getElementById('log');
                    logDiv.innerHTML = '';
                    data.log.forEach(entry => {
                        const p = document.createElement('p');
                        p.textContent = `${entry.name} - ${entry.event_type} at ${entry.time}`;
                        logDiv.appendChild(p);
                    });
                });
            });
        </script>
    </head>
    <body>
        <div>
            <h1>Checked-In Users</h1>
            <input id="search-bar" type="text" placeholder="Search for a user...">
            <p><strong>Total Users:</strong> <span id="total-users">0</span></p>
            <p><strong>Log (Most Recent to Oldest):</strong></p>
            <div id="log">No users checked in yet.</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@socketio.on('request_initial_log')
def handle_initial_log_request():
    db = get_local_session()
    try:
        user_log = get_all_check_ins(db)
        emit('update_log', {'log': user_log, 'total_users': len(user_log)})
    finally:
        db.close()


@socketio.on('search_log')
def handle_search_log(data):
    db = get_local_session()
    try:
        query = data.get('query', '').strip()
        if not query:
            user_log = get_all_check_ins(db)
            emit('search_results', {'log': user_log, 'total_users': len(user_log)})
            return

        # Search check-in logs
        filtered_log = search_check_ins(db, query)

        emit('search_results', {
            'log': filtered_log,
            'total_users': len(filtered_log)
        })

    except Exception as e:
        emit('notification', {
            'success': False,
            'message': f'Search error: {str(e)}'
        })
    finally:
        db.close()


@app.route('/delete_log_entry', methods=['POST'])
def delete_log_entry():
    db = get_local_session()
    try:
        data = request.json
        user_id = data['user_id']
        event_type = data['event_type']

        # Delete the check-in entry
        success = delete_check_in(db, user_id, event_type)

        if success:
            # Get updated log and broadcast
            user_log = get_all_check_ins(db)
            socketio.emit('update_log', {
                'log': user_log,
                'total_users': len(user_log)
            })
            return jsonify({'message': 'Log entry deleted successfully'}), 200
        else:
            return jsonify({'error': 'Log entry not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)
