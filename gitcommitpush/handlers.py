from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
import distutils
import os, json, git, urllib, requests
from git import Repo, GitCommandError
from subprocess import check_output


class ErrorPrintToJupyter(Exception):
    pass


class git_cnxn:
    """connection to git remote.
    Currently tested with GitHub and GitLab.
    """
    def __init__(self):
        # get parameters from environment variables
        # expand variables since Docker's will pass VAR=$VAL as $VAL without expansion
        try:
            self.dir_parent = os.path.expandvars(os.environ.get('GIT_PARENT_DIR'))
        except TypeError as e:
            raise TypeError(
                "Did you remember to source env.sh?\n{}".format(e))
        self.repo_nm = os.path.expandvars(os.environ.get('GIT_REPO_NAME'))
        if self.repo_nm:
            self.dir = os.path.join( self.dir_parent, self.repo_nm)
        else:
            self.dir = self.dir_parent
        self.url = os.path.expandvars(os.environ.get('GIT_REMOTE_URL'))
        self.user = os.path.expandvars(os.environ.get('GIT_USER'))
        self.repo_upstream = os.path.expandvars(os.environ.get('GIT_REMOTE_UPSTREAM'))
        self.branch_nm = os.path.expandvars(os.environ.get('GIT_BRANCH_NAME'))
        self.remote_nm = os.path.expandvars(os.environ.get('GIT_REMOTE_NAME'))
        if not self.remote_nm:
            self.remote_nm = "origin"
        self.access_token = os.path.expandvars(os.environ.get('GITHUB_ACCESS_TOKEN'))
        # get cwd
        self.cwd = os.getcwd()

        # checkout repo
        try:
            os.chdir(self.dir)
            # make sure its a git repo and get Repo
            dir_repo = check_output(['git','rev-parse','--show-toplevel']).strip()
            self.repo = Repo(dir_repo.decode('utf8'))
            # put back cwd
            os.chdir(self.cwd)
        except GitCommandError as e:
            raise ErrorPrintToJupyter(
                "Could not checkout repo: {}\n{}".format(dir_repo, e))

        self.branch = self.select_or_create_branch()
        self.remote = self.select_or_create_remote()

    def select_or_create_branch(self):
        # create or select branch
        try:
            print(self.repo.git.checkout('HEAD', b=self.branch_nm))
        except GitCommandError:
            print("Switching to {}".format(self.repo.heads[self.branch_nm].checkout()))
        return self.branch_nm

    def select_or_create_remote(self):
        # create or switch to remote
        try:
            remote = self.repo.create_remote(self.remote_nm, self.url)
        except GitCommandError:
            print("Remote {} already exists...".format(self.remote_nm))
            remote = self.repo.remote(self.remote_nm)
        return remote

    def add(self, filename, add_all=False):
        """Performs git add of filename.
        Git returns nothing if good or no add
        """
        try:
            print(self.repo.git.add(self.dir + filename, A=add_all))
            if add_all:
                print('Adding All')
                print(self.repo.git.add(A=True))
            # filname from js includes '/' ex. '/name'
        except GitCommandError as e:
            print(e)
            raise ErrorPrintToJupyter(
                    "Could not add changes to notebook: {}\n{}".format(
                        self.dir + filename, e))

    def commit(self, msg):
        # commit current notebook
        # client will sent pathname containing git directory; append to git directory's parent
        staged = [fil.a_path for fil in self.repo.index.diff("HEAD")]
        print('Staged:', staged)
        try:
            print(self.repo.git.commit(
                m="{}\n\nUpdated {}".format(msg, staged) ))
        except GitCommandError as e:
            if 'directory clean' in str(e):
                raise ErrorPrintToJupyter(
                        'Nothing to Commit!\nDid you save first?\nCarry On.')
            raise ErrorPrintToJupyter(
                    "Could not commit changes to notebook: {}\n{}".format(
                        staged, e))

    def pull(self):
        try:
            out = self.repo.git.pull()
            print("git.pull: {}".format(out))
        #will need to handle merge issues......
        except Exception as e:
            raise ErrorPrintToJupyter("Error during Pull {}".format(e))


    def push(self):
        try:
            pushed = self.remote.push(self.branch_nm)
            assert len(pushed)>0
            assert pushed[0].flags in [
                git.remote.PushInfo.UP_TO_DATE,
                git.remote.PushInfo.FAST_FORWARD,
                git.remote.PushInfo.NEW_HEAD,
                git.remote.PushInfo.NEW_TAG]
        except GitCommandError as e:
            raise ErrorPrintToJupyter(
                "Could not push to remote {}\n{}".format(self.remote, e))
        except AssertionError as e:
            raise ErrorPrintToJupyter(
                "Could not push to remote {}: {}\n{}".format(
                    self.remote, pushed[0].summary, e))
        print('Pushed to {} {}'.format(self.remote, pushed[0].summary))

    def make_pr(self):
        """holdover from sat28/githubcommit not in use"""
        # open pull request
        try:
            github_url = "https://api.github.com/repos/{}/pulls".format(self.repo_upstream)
            github_pr = {
                "title":"{} Notebooks".format(self.user),
                "body":"IPython notebooks submitted by {}".format(self.user),
                "head":"{}:{}".format(self.user, self.remote),
                "base":"master"
            }
            github_headers = {"Authorization": "token {}".format(self.access_token)}
            r = requests.post(self.github_url, data=json.dumps(self.github_pr),
                    headers=self.github_headers)
            if r.status_code != 201:
                print("Error submitting Pull Request to {}".format(self.repo_upstream))
        except:
            print("Error submitting Pull Request to {}".format(self.repo_upstream))


class GitCommitHandler(IPythonHandler):

    def error_and_return(self, dirname, reason):

        # send error
        self.send_error(500, reason=reason)

        # return to directory
        os.chdir(dirname)

    def put(self):
        """action sent from js. Does all the work!"""

        # get current directory (to return later)
        #might not be needed
        cwd = os.getcwd()

        try:
            # make connection to git remote server
            git = git_cnxn()

            # obtain filename and msg for commit
            data = json.loads(self.request.body.decode('utf-8'))
            filename = urllib.parse.unquote(data['filename'])
            msg = data['msg']
            add_all = data['add_all']

            git.pull()
            git.add(filename, add_all)
            git.commit(msg)
            git.push()
            #git_pr()

            # return to directory
            os.chdir(cwd)

            # close connection
            self.write(
                {'status': 200,
                'statusText': ('Success!  '
                    'Changes to {} captured on branch {} at {}'.format(
                        filename, git.branch_nm, git.url))
                })
        except ErrorPrintToJupyter as e:
            self.error_and_return(cwd, str(e).replace('\n', '</br> '))



def setup_handlers(nbapp):
    route_pattern = ujoin(nbapp.settings['base_url'], '/git/commit')
    nbapp.add_handlers('.*', [(route_pattern, GitCommitHandler)])

