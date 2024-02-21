config-pin P9_11 gpio
config-pin P9_13 gpio
config-pin P9_17 gpio
config-pin P9_19 gpio
cd ~/sys/class/gpio
echo 5 > export
echo 13 > export
cd gpio5
echo "out" > direction
cd ../gpio13
echo "out" > direction
# need usb setup