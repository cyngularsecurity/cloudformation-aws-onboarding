#!/usr/bin/env bash


# Verify the current directory and switch if necessary
if [[ "$(pwd)" != "/home/ubuntu/main" ]]; then
  cd /home/ubuntu/main
fi

# services and their respective ports
declare -A services=(
  ["8206"]="auth-service"
  ["80"]="overview-service"
  ["81"]="incidents-service"
  ["82"]="investigation-service"
  ["83"]="visibility-service"
  ["84"]="settings-service"
  ["85"]="general-service"
)

log_file="/home/ubuntu/main/services_watchdog.log"

# (watch_dog)
# check the services
for port in "${!services[@]}"; do
  # check if the service is running
  if ! lsof -t -i:${port} > /dev/null; then
    # if the service is not running, go to its directory
    cd ${services[$port]}
    # Start the service
    nohup npm start &
    # Go back to the main directory
    cd ..
    # log the service start
    echo "$(date): ${services[$port]} was not running, started it on port ${port}" >> $log_file
  fi
done


# # Change these variables
# APP_URL="http://your-node-app-url.com"
# LOG_FILE="/path/to/log/file.log"

# # Perform the check
# response=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL)

# if [ "$response" -eq 200 ]; then
#     echo "$(date): Node app is up and running" >> $LOG_FILE
# else
#     echo "$(date): Node app is not responding (HTTP status code: $response)" >> $LOG_FILE
#     # Restart your app here if needed
#     # Example: pm2 restart your-app-name
# fi
