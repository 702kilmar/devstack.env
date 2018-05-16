masakari segment-list
#
masakari segment-create --name test1 --recovery-method auto --service-type auto                 
#
masakari host-create --name `hostname` --segment-id test1 --type auto --control-attributes auto 
