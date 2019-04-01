#!/usr/bin/python2
# -*-coding:utf-8-*-

import os
import commands
import numpy as np
import sys
import csv
import pandas as pd
import time
from pyecharts.engine import create_default_environment
from pandas import DataFrame as df
from pyecharts import Bar3D
from pyecharts import Line, Bar
from pyecharts import Grid
from pyecharts import Page
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr

import smtplib
import re

VDBENCH_DIR = ''
DEV = ''
TEST_TYPE = ''
DATA_VALIDATION = ''


class Vdrunner(object):
    def __init__(self, case_no, vdbench_cfg, precondition_cfg=None):
        self.case_no = case_no
        self.vdbench_cfg = vdbench_cfg
        self.precondition_cfg = precondition_cfg

    def create_cfg(self, flag):
        if flag == 'precondition':
            with open('precondition.cfg', 'w') as f:
                f.write(self.precondition_cfg.replace('%s', DEV))
        elif flag == 'vdbench':
            with open('%s.cfg' % self.case_no, 'w') as f:
                f.write(self.vdbench_cfg.replace('%s', DEV))
        else:
            print('传入参数值有误！')

    def exec_precondition(self):
        if TEST_TYPE == 'Trim':
            self.exec_trimprecondition()
        if TEST_TYPE == 'Security':
            self.exec_seprecondition()
        if TEST_TYPE == 'Format':
            self.exec_formatprecondition()
        else:
            self.exec_normalprecondition()

    def exec_normalprecondition(self):
        self.exec_secuerase()
        if self.precondition_cfg:
            self.create_cfg('precondition')
            if DATA_VALIDATION=='YES':
                (status, output) = commands.getstatusoutput('%s/vdbench  -vr -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            else:
                (status, output) = commands.getstatusoutput('%s/vdbench -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            print(status)
        self.check_errlog('precondition')

    def exec_trimprecondition(self):
        if self.precondition_cfg:
            if DATA_VALIDATION=='YES':
                (status, output) = commands.getstatusoutput('%s/vdbench  -vr -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            else:
                (status, output) = commands.getstatusoutput('%s/vdbench -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            print(status)
        self.check_errlog('precondition')
        self.exec_trim()

    def exec_formatprecondition(self):
        if self.precondition_cfg:
            self.create_cfg('precondition')
            if DATA_VALIDATION=='YES':
                (status, output) = commands.getstatusoutput('%s/vdbench  -vr -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            else:
                (status, output) = commands.getstatusoutput('%s/vdbench -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            print(status)
        self.check_errlog('precondition')
        self.exec_format()

    def exec_seprecondition(self):
        if self.precondition_cfg:
            self.create_cfg('precondition')
            if DATA_VALIDATION=='YES':
                (status, output) = commands.getstatusoutput('%s/vdbench  -vr -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            else:
                (status, output) = commands.getstatusoutput('%s/vdbench -f precondition.cfg  -o precondition ' % (
                    VDBENCH_DIR))
            print(status)
        self.check_errlog('precondition')
        self.exec_secuerase()

    def exec_secuerase(self):
        cmd = "lsscsi -g | grep %s |awk -F ' ' '{print $NF}' " % DEV
        (status, self.sgx) = commands.getstatusoutput(cmd)
        cmd1 = 'hdparm --user-master u --security-set-pass 123456 %s' % DEV
        cmd2 = 'hdparm --user-master u --security-erase 123456 %s' % self.sgx
        (status, output1) = commands.getstatusoutput(cmd1)
        if status == 0 and 'Issuing SECURITY_SET_PASS command, password="123456", user=user, mode=high' in output1:
            (status, output2) = commands.getstatusoutput(cmd2)
            if 'Issuing SECURITY_ERASE command, password="123456", user=user' not in output2:
                with open('log.txt', 'wb') as f:
                    f.write(output2)
                sys.exit()
        else:
            with open('log.txt', 'wb') as f:
                f.write(output1)
            sys.exit()
        if status != 0:
            sys.exit()

    def exec_trim(self):
        cmd = 'fio  --filename=%s --rw=trim --bs=1G --name=test' % DEV
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            sys.exit()

    def exec_format(self):
        cmd = 'mkfs.ext4 %s' % DEV
        (status, output) = commands.getstatusoutput(cmd)
        if status != 0:
            sys.exit()

    def exec_vdbench(self):
        self.create_cfg('vdbench')
        if DATA_VALIDATION=='YES':
            (status, output) = commands.getstatusoutput('%s/vdbench -vr -f %s.cfg  -o %s ' % (
                VDBENCH_DIR, self.case_no, self.case_no))
        else:
            (status, output) = commands.getstatusoutput('%s/vdbench -f %s.cfg  -o %s ' % (
                VDBENCH_DIR, self.case_no, self.case_no))

        self.check_errlog(self.case_no)

    def check_errlog(self, type):
        self.errodatas = []
        with open('%s/errorlog.html' % type, "r") as read_f:
            for res in read_f:
                if "Exception" in res:
                    self.errodatas.append('%s/%s/errorlog.html' % (os.getcwd(), type))
                    self.errodatas.append(res)
        with open('%s/logfile.html' % type, "r") as read_f:
            for res in read_f:
                if "Exception" in res:
                    self.errodatas.append('%s/%s/logfile.html' % (os.getcwd(), type))
                    self.errodatas.append(res)
        self.errodatas = ''.join(self.errodatas)
        if self.errodatas:
            send_mail(MAIL_ACCOUNT, MAIL_ACCOUNT, "mail.xitcorp.com", MAIL_PASSWD,
                      (u'vdbench测试执行报错！%s' % self.errodatas))
            sys.exit()

    def filter(self, res):
        r = re.compile(r'^[a-zA-Z]')
        for item in res:
            result = r.match(item)
            if result != None:
                return 1
        return 0

    def get_summarydata(self):
        self.datas = [
            ['Time', 'Interval', 'IOPS', 'Bandwidth', 'BytesIO', 'Readpct', 'Latency', 'Readresp', 'Writeresp',
             'Respmax', 'Respstddev', 'Quenedepth', 'Cpusys+u', 'Cpusys']]
        with open('%s/summary.html' % (self.case_no), 'r') as read_f:
            tag = False
            for res in read_f:
                res.encode()
                if self.filter(res) or 'Reached maxdata' in res:
                    tag = True
                    continue
                if tag and res.strip():
                    self.datas.append(res.split())

        with open('%s_summary.csv' % (self.case_no), "wb")as out:
            csv_write = csv.writer(out, dialect='excel')
            for row in self.datas:
                csv_write.writerow(row)


class Plot(object):
    def __init__(self, case_no, case_name):
        self.case_no = case_no
        self.case_name = case_name

    def get_data(self, col):
        self.col = col
        self.data = []
        with open('%s_summary.csv' % (self.case_no), 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            self.data = [float(row[self.col]) for row in csv_reader]
        return self.data

    def plot_totallines(self):
        self.IOPS = self.get_data('IOPS')
        self.Bandwidth = self.get_data('Bandwidth')
        self.Latency = self.get_data('Latency')
        x_IOPS = [i for i in range(len(self.IOPS))]
        x_Bandwidth = [i for i in range(len(self.Bandwidth))]
        x_Latency = [i for i in range(len(self.Latency))]
        line1 = Line(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', title_pos='center',
                     width='1600px', height='600px',
                     subtitle_color='rgba(97, 160, 168, 1)', title_text_size=20, subtitle_text_size=16, title_top=100)
        line2 = Line(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', width='1600px', height='600px',
                     subtitle_color='rgba(97, 160, 168, 1)', title_text_size=20, title_pos='center',
                     subtitle_text_size=16, title_top=900)
        line3 = Line(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', title_pos='center',
                     width='1600px', height='600px',
                     subtitle_color='rgba(97, 160, 168, 1)', title_text_size=20, subtitle_text_size=16, title_top=1700)
        line1.add('IOPS_summary', x_IOPS, self.IOPS,
                  is_smooth=True,
                  line_width=1,
                  mark_point=['min', 'average', 'max'],
                  mark_point_symbol=['roundRect'],
                  xaxis_name='Time',
                  legend_top=180,
                  legend_text_size=10,
                  is_more_utils=True,
                  legend_pos='center')
        line2.add('Bandwidth_summary', x_Bandwidth, self.Bandwidth,
                  is_smooth=True,
                  line_width=1,
                  mark_point=['min', 'average', 'max'],
                  mark_point_symbol=['roundRect'],
                  xaxis_name='Time',
                  legend_top=980,
                  legend_text_size=10,
                  legend_pos='center')
        line3.add('Latency_summary', x_Latency, self.Latency,
                  is_smooth=True,
                  line_width=1,
                  mark_point=['min', 'average', 'max'],
                  mark_point_symbol=['roundRect'],
                  xaxis_name='Time',
                  legend_top=1780,
                  legend_text_size=10,
                  legend_pos='center')
        grid = Grid(height=2700, width=2000)
        grid.add(line1, grid_top=200, grid_bottom=1900, grid_left=60)
        grid.add(line2, grid_top=1000, grid_bottom=1100, grid_left=60)
        grid.add(line3, grid_top=1800, grid_bottom=300, grid_left=60)
        return grid

    def plot_lines(self):
        self.get_data('IOPS')
        self.linechart()
        self.get_data('Bandwidth')
        self.linechart()
        self.get_data('Latency')
        self.linechart()

    def scatterchart(self):
        x = [i for i in range(len(self.data))]
        y = self.data
        scatter = Scatter(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', title_pos='left',
                          width='1600px', height='800px',
                          subtitle_color='rgba(97, 160, 168, 1)', title_text_size=16, subtitle_text_size=14,
                          title_top=0)
        scatter.add('%s_summary' % (self.col), x, y,
                    is_smooth=True,
                    line_width=1,
                    mark_point=['min', 'average', 'max'],
                    mark_point_symbol=['roundRect'],
                    xaxis_name='Time',
                    legend_top=30,
                    legend_text_size=14,
                    is_more_utils=True,
                    legend_pos='center')
        env = create_default_environment('html')
        env.render_chart_to_file(scatter, path='%s_%s_summary.html' % (self.case_no, self.col))

    def plot_totalscatters(self):
        self.IOPS = self.get_data('IOPS')
        self.Bandwidth = self.get_data('Bandwidth')
        self.Latency = self.get_data('Latency')
        x_IOPS = [i for i in range(len(self.IOPS))]
        x_Bandwidth = [i for i in range(len(self.Bandwidth))]
        x_Latency = [i for i in range(len(self.Latency))]
        scatter1 = Scatter(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', title_pos='center',
                           width='1600px', height='600px',
                           subtitle_color='rgba(97, 160, 168, 1)', title_text_size=20, subtitle_text_size=16,
                           title_top=100)
        scatter2 = Scatter(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', width='1600px',
                           height='600px',
                           subtitle_color='rgba(97, 160, 168, 1)', title_text_size=20, title_pos='center',
                           subtitle_text_size=16, title_top=900)
        scatter3 = Scatter(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', title_pos='center',
                           width='1600px', height='600px',
                           subtitle_color='rgba(97, 160, 168, 1)', title_text_size=20, subtitle_text_size=16,
                           title_top=1700)
        scatter1.add('IOPS_summary', x_IOPS, self.IOPS,
                     is_smooth=True,
                     line_width=1,
                     mark_point=['min', 'average', 'max'],
                     mark_point_symbol=['roundRect'],
                     xaxis_name='Time',
                     legend_top=180,
                     legend_text_size=10,
                     is_more_utils=True,
                     legend_pos='center')
        scatter2.add('Bandwidth_summary', x_Bandwidth, self.Bandwidth,
                     is_smooth=True,
                     line_width=1,
                     mark_point=['min', 'average', 'max'],
                     mark_point_symbol=['roundRect'],
                     xaxis_name='Time',
                     legend_top=980,
                     legend_text_size=10,
                     legend_pos='center')
        scatter3.add('Latency_summary', x_Latency, self.Latency,
                     is_smooth=True,
                     line_width=1,
                     mark_point=['min', 'average', 'max'],
                     mark_point_symbol=['roundRect'],
                     xaxis_name='Time',
                     legend_top=1780,
                     legend_text_size=10,
                     legend_pos='center')
        grid = Grid(height=2700, width=2000)
        grid.add(scatter1, grid_top=200, grid_bottom=1900, grid_left=60)
        grid.add(scatter2, grid_top=1000, grid_bottom=1100, grid_left=60)
        grid.add(scatter3, grid_top=1800, grid_bottom=300, grid_left=60)
        return grid

    def linechart(self):
        x = [i for i in range(len(self.data))]
        y = self.data
        line1 = Line(self.case_no, self.case_name, title_color='rgba(47, 69, 84, 1)', title_pos='left',
                     width='1600px', height='800px',
                     subtitle_color='rgba(97, 160, 168, 1)', title_text_size=16, subtitle_text_size=14, title_top=0)
        line1.add('%s_summary' % (self.col), x, y,
                  is_smooth=True,
                  line_width=1,
                  mark_point=['min', 'average', 'max'],
                  mark_point_symbol=['roundRect'],
                  xaxis_name='Time',
                  legend_top=30,
                  legend_text_size=14,
                  is_more_utils=True,
                  legend_pos='center')
        env = create_default_environment('html')
        env.render_chart_to_file(line1, path='%s_%s_summary.html' % (self.case_no, self.col))

    def plot_scatters(self):
        self.get_data('IOPS')
        self.scatterchart()
        self.get_data('Bandwidth')
        self.scatterchart()
        self.get_data('Latency')
        self.scatterchart()


def read_excel(casedir):
    # reload(sys)
    # sys.setdefaultencoding('utf-8')
    df = pd.DataFrame(pd.read_excel(casedir))
    return df


def updata_tag(casedir, index, colname):
    df = pd.DataFrame(pd.read_excel(casedir))
    df.loc[index, colname] = 'PASS'
    df.to_excel(casedir, header=True, index=False)


def send_mail(from_addr, to_addr, smtp_server, password, content):
    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = _format_addr('vdbench测试结果 <%s>' % from_addr)
    msg['To'] = _format_addr('测试执行人员 <%s>' % to_addr)
    msg['Subject'] = Header('vdbench测试结果，请及时处理！', 'utf-8').encode()
    server = smtplib.SMTP(smtp_server, 25)
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()


def get_confvalue(key):
    with open('config.txt', 'r') as f:
        for line in f:
            if line.startswith(key):
                return line.strip('\r\n').split('=')[1]


def check_device():
    cmd = "df -h | grep -w / |awk '{print $1}'  "
    (status, output) = commands.getstatusoutput(cmd)
    print (output)
    if status != 0:
        sys.exit()
    if DEV in output:
        print('Error：当前测试盘为系统盘，请确认后再进行测试！')
        sys.exit()


if __name__ == '__main__':
    VDBENCH_DIR = get_confvalue('VDBENCH_DIR')
    DEV = get_confvalue('DEV')
    TYPE = get_confvalue('TEST_TYPE')
    FILE_NAME = get_confvalue('FILE_NAME').decode('utf-8')
    MAIL_ACCOUNT = get_confvalue('MAIL_ACCOUNT')
    RUN_LEVEL = get_confvalue('RUN_LEVEL')
    MAIL_PASSWD = get_confvalue('MAIL_PASSWD')
    DATA_VALIDATION = get_confvalue('DATA_VALIDATION')
    print('Please confirm that the test data is correct:')
    print (VDBENCH_DIR, DEV, TYPE, FILE_NAME, CHECK_DATA, RUN_LEVEL, MAIL_ACCOUNT, MAIL_PASSWD)
    exc = raw_input('Please choose run or not(y/n):')
    if exc == 'n':
        sys.exit()
    PY_DIR = os.getcwd()
    page = Page()
    check_device()
    data = read_excel('%s/%s' % (PY_DIR, FILE_NAME))
    if RUN_LEVEL == 'run_flag':
        for index, rows in data.iterrows():
            if rows['run_flag'] == 'YES':
                os.mkdir('%s/%s' % (PY_DIR, rows['Case No.']))
                os.chdir('%s/%s' % (PY_DIR, rows['Case No.']))
                vdbench_cfg = rows['vdbench_cfg'].split('====')
                for cfg in vdbench_cfg:
                    print cfg
                    if pd.isnull(rows['precondition_cfg']):
                        vd = Vdrunner('%s_%s' % (rows['Case No.'], vdbench_cfg.index(cfg)), cfg.strip())
                    else:
                        vd = Vdrunner('%s_%s' % (rows['Case No.'], vdbench_cfg.index(cfg)), cfg.strip(),
                                      rows['precondition_cfg'])
                        vd.exec_precondition()
                    vd.exec_vdbench()
                    vd.get_summarydata()
                    p = Plot('%s_%s' % (rows['Case No.'], vdbench_cfg.index(cfg)), rows['name'])
                    p.plot_scatters()
                    page.add(p.plot_totalscatters())
                updata_tag('%s/%s' % (PY_DIR, FILE_NAME), index, 'run_flag')
    else:
        for index, rows in data.iterrows():
            if rows['run_level'] == RUN_LEVEL:
                os.mkdir('%s/%s' % (PY_DIR, rows['Case No.']))
                os.chdir('%s/%s' % (PY_DIR, rows['Case No.']))
                vdbench_cfg = rows['vdbench_cfg'].split('====')
                for cfg in vdbench_cfg:
                    print cfg
                    if pd.isnull(rows['precondition_cfg']):
                        vd = Vdrunner('%s_%s' % (rows['Case No.'], vdbench_cfg.index(cfg)), cfg.strip())
                    else:
                        vd = Vdrunner('%s_%s' % (rows['Case No.'], vdbench_cfg.index(cfg)), cfg.strip(),
                                      rows['precondition_cfg'])
                        vd.exec_precondition()
                    vd.exec_vdbench()
                    vd.get_summarydata()
                    p = Plot('%s_%s' % (rows['Case No.'], vdbench_cfg.index(cfg)), rows['name'])
                    p.plot_scatters()
                    page.add(p.plot_totalscatters())
            updata_tag('%s/%s' % (PY_DIR, FILE_NAME), index, 'run_flag')

    os.chdir(PY_DIR)
    page.render('%s.html' % FILE_NAME)
    commands.getstatusoutput('tar -zcf  vdbench.tar.gz  *')
    content = (u'vdbench脚本测试成功，请到%s目录下载测试结果压缩包vdbench.tar.gz' % PY_DIR)
    send_mail(MAIL_ACCOUNT, MAIL_ACCOUNT, "mail.xitcorp.com", MAIL_PASSWD, content)
