# smart_chair
smart IoT chair

amazon cloud documentation: https://github.com/rost5000/springboot-datacollector-smartchair

In order to run code on Raspberry Pi go to *raspberry_code* and run

```
python SimpleRequest.py --label 'usual table sitting 0' --peopleId 'anton' --timestep_detect 0.1 --max_time 60
```

By default batches with data are sended to a server every 10 seconds. 
