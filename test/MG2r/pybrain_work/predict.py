from pybrain.tools.shortcuts import buildNetwork
from pybrain.datasets import SupervisedDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.structure import TanhLayer

target_size = 1
hidden_layers = 3
input_size = 3

# [ (-O2;-O3)*5, (UL;No UL)*2, (PF; No FL)*1 ]
rawdata = []
rawdata.append(([0, 0, 0], [300.0]))
rawdata.append(([0, 0, 1], [200.0]))
rawdata.append(([0, 1, 0], [100.0]))
rawdata.append(([0, 1, 1], [0.0]))
rawdata.append(([1, 0, 0], [800.0]))
rawdata.append(([1, 0, 1], [700.0]))
rawdata.append(([1, 1, 0], [600.0]))

net = buildNetwork( input_size, hidden_layers, target_size, bias = True )
trainer = BackpropTrainer(net, momentum=0.1, weightdecay=0.01, learningrate=0.01)

ds = SupervisedDataSet( input_size, target_size )
#for i, t in rawdata[:4]:
#    ds.appendLinked( i, t )

#for i, t in rawdata[4:]:
for i, t in rawdata:
    ds.appendLinked( i, t )
    trainer.trainOnDataset(ds)
    #trainer.trainUntilConvergence(dataset=ds)
    ds_e = SupervisedDataSet( input_size, target_size )
    ds_e.appendLinked( [1, 1, 1], None )
    e = net.activateOnDataset( ds_e )
    print 'Estimation should near 500.0, but %f'%e

#import pdb; pdb.set_trace()
