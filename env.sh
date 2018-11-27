###################### GIT PARAMETERS #####################################
export GIT_PARENT_DIR=~
export GIT_REPO_NAME=#your-repo
export GIT_BRANCH_NAME=#your-branch
export GIT_REMOTE_NAME=#your-branch (origin)
export GIT_USER=#your-gituser
export GIT_EMAIL=#your-email
export GITHUB_ACCESS_TOKEN=#access-token from github developer settings
export GIT_USER_UPSTREAM=#your-user

export GIT_SERVER=git@github.com 
export GIT_HTTP=https://github.com

############################################################################
#### Derived Variables
############################################################################
export GIT_REMOTE_URL=$GIT_SERVER:$GIT_USER/$GIT_REPO_NAME.git
export GIT_REMOTE_URL_HTTPS=$GIT_HTTP/$GIT_USER/$GIT_REPO_NAME.git
export GIT_REMOTE_UPSTREAM=$GIT_USER_UPSTREAM/$GIT_REPO_NAME

####################### Git Repo where notebooks will be pushed ############
cd $GIT_PARENT_DIR && git clone $GIT_REMOTE_URL_HTTPS

####################### SSH KEY FOR GIT ###################################
# add to known host ...?
# https://serverfault.com/questions/132970/can-i-automatically-add-a-new-host-to-known-hosts
# ssh-keygen -t rsa && ssh-keygen -y -f ~/.ssh/id_rsa > ~/.ssh/id_rsa.pub &&
eval $(ssh-agent -s)
# eval `ssh-agent`
ssh-add /opt/jupyter/.ssh/id_rsa
####################### To be added to git account settings ################

####################### Change in jupyter config ###########################
if [ ! -f ~/.jupyter/jupyter_notebook_config.py ]; then
   jupyter notebook --generate-config
fi

echo 'c.NotebookApp.disable_check_xsrf = True' >> ~/.jupyter/jupyter_notebook_config.py

cp $GIT_PARENT_DIR/githubcommit/config ~/.ssh/config
