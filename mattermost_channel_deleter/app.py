#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import argparse
import subprocess

import mysql.connector


logger = logging.getLogger(__name__)



class MySQLCursorDict(mysql.connector.cursor.MySQLCursor):
    """assoc fetch for mysql.connect"""
    def _row_to_python(self, rowdata, desc=None):
        row = super(MySQLCursorDict, self)._row_to_python(rowdata, desc)
        if row:
            return dict(zip(self.column_names, row))
        return None


class ArgparseDirFullPaths(argparse.Action):
    """Expand user- and relative-paths"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))


def argparse_is_dir(dirname):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname


def setup_logging(debug=False):
    """Configure logging to stdout."""
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)

    stdout_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    stdout_handler.setLevel(logging.INFO)
    if debug:
        stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(stdout_formatter)

    root.addHandler(stdout_handler)



class App:

    def __init__(self):
        """
        This function gets called when initing the class
        """
        pass


    def main(self):
        """
        Main function which controls the app
        """
        self.parse_args()
        setup_logging(self.args.debug)
        self.parse_config()
        self.connect_db()
        self.delete_old_channels()


    def parse_args(self):
        """
        parses the arguments passed to the script
        """
        parser = argparse.ArgumentParser(
            description="Mattermost user purger"
        )
        parser.add_argument(
            "--config",
            type=argparse.FileType("r"),
            required=True
        )
        parser.add_argument(
            "--mattermost-root",
            type=argparse_is_dir,
            action=ArgparseDirFullPaths,
            required=True
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            default=False
        )
        self.args = parser.parse_args()


    def parse_config(self):
        """
        parses given mattermost config and extracts
        database and ldap connection
        """

        self.mm_config = json.load(self.args.config)

        # this part is pretty ugly but works for now
        sqlpath = self.mm_config['SqlSettings']['DataSource']
        self.db_user, self.db_pass = sqlpath.split('@')[0].split(":")
        self.db_host, self.db_port = sqlpath[sqlpath.find("(")+1:sqlpath.find(")")].split(":")
        self.db_name = sqlpath[sqlpath.find(")/")+2:sqlpath.find("?")]

        # set mattermost cli path
        self.mm_cli_path = os.path.join(
            self.args.mattermost_root,
            "bin/mattermost"
        )


    def connect_db(self):
        """
        connects to the database and exits the app
        if something is wrong
        """
        try:
            self.db_connection = mysql.connector.connect(
                user=self.db_user,
                password=self.db_pass,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name
            )
            self.db_cursor = self.db_connection.cursor(cursor_class=MySQLCursorDict)
        except:
            logger.error("cannot connect to database")
            sys.exit(1)

        logger.debug("connected database: {0}/{1} as user {2}".format(
            self.db_host,
            self.db_name,
            self.db_user
        ))


    def get_team_from_id(self, teamid):
        self.db_cursor.execute("select Name from Teams where id='{0}'".format(
            teamid
        ))
        res = self.db_cursor.fetchall()
        return res[0]['Name']


    def delete_old_channels(self):
        """
        this function does the actual deletion of users
        """

        # fetch list of all disabled users in mattermost
        self.db_cursor.execute("SELECT * FROM Channels WHERE DeleteAt>0 and Name LIKE 'deleted-%'")
        delete_candidates = self.db_cursor.fetchall()

        # loop over all delete candidates
        for channel in delete_candidates:
            team_name = self.get_team_from_id(channel["TeamId"] )
            if not self.args.dry_run:
                self.delete_mm_channel(channel, team_name)
            else:
                logger.info("Would delete channel with name={0} and ID={1}".format(
                    channel['Name'],
                    channel['Id']
                ))

    def delete_mm_channel(self, channel, team_name):
        """
        delete the channel over the mattermost cli interface
        """

        logger.info("deleting channel with name={0} and ID={1}".format(
            channel['Name'],
            channel['Id']
        ))
        cmd = [
            self.mm_cli_path,
            "channel",
            "delete",
            "{0}:{1}".format(team_name, channel['Name']),
            "--confirm"
        ]
        subprocess.check_output(cmd)




def main():
    app = App()
    app.main()

if __name__ == '__main__':
    main()
