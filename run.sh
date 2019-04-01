apt install python-pip
pip install numpy
pip install pandas
pip install pyecharts
pip install xlrd
pip install openpyxl
apt install tmux
chmod +x vdbench.py
tmux new-session -d -s test && tmux send -t test 'python vdbench.py' ENTER 
