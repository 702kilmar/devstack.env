#/bin/bash
git config --global user.email "louie.kwan@windriver.com"
git config --global user.name "Louie Kwan"
git config --global gitreview.username "lkwan"
git config --global core.editor "vim"

#
git clone https://git.openstack.org/openstack-dev/sandbox.git ~/sandbox
#
git clone https://git.openstack.org/openstack-dev/devstack ~/devstack
#
cp `pwd`/local.conf ~/devstack
