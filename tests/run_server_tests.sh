#!/bin/sh
# Runs the real-server tests with a fresh temporary database each time.
cd "$(dirname "$0")/.." || exit 1
for t in server_api server_e2e server_admin_flows server_login_ui server_roles_ui server_features server_features_ui csp_sweep server_extras server_login_v14 server_policy server_login_page server_setup; do
  rm -rf /tmp/shagar_t
  python3 server/server.py --port 8800 --data /tmp/shagar_t --owner-password 'Sunrise-Tea-4471' --rate-scale 50 >/tmp/shagar_server.log 2>&1 &
  PID=$!
  sleep 2
  python3 tests/$t.py | tail -90
  kill $PID 2>/dev/null
  wait $PID 2>/dev/null
done
rm -rf /tmp/shagar_rl
python3 server/server.py --port 8801 --data /tmp/shagar_rl --owner-password 'Sunrise-Tea-4471' >/tmp/shagar_server_rl.log 2>&1 &
PID=$!
sleep 2
python3 tests/server_ratelimit.py
kill $PID 2>/dev/null
wait $PID 2>/dev/null
rm -rf /tmp/shagar_load
python3 server/server.py --port 8802 --data /tmp/shagar_load --owner-password 'Sunrise-Tea-4471' --rate-scale 1000 --no-auto-backup >/tmp/shagar_server_load.log 2>&1 &
PID=$!
sleep 2
python3 tests/load_check.py | tail -12
kill $PID 2>/dev/null
wait $PID 2>/dev/null
