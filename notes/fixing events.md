from psutil._pslinux import calculate_avail_vmem
from IPython.lib.clipboard import wayland_clipboard_get
MOCKLSL stream:
Connected to MockEEG at 250.0 Hz
timestamps[0] 1310208.3902859
timestamps[0] 1310209.3885666002
timestamps[0] 1310210.3808486
event added: 1310212.3397314 3
timestamps[0] 1310211.3812902002
timestamps[0] 1310212.3834359
timestamps[0] 1310213.3917938
timestamps[0] 1310214.3888447
timestamps[0] 1310215.3894187
timestamps[0] 1310216.389446
timestamps[0] 1310217.4126113001
timestamps[0] 1310218.4056282002
timestamps[0] 1310219.4265841001
event added: 1310222.3617574 1
timestamps[0] 1310220.4260166
timestamps[0] 1310221.4352037
timestamps[0] 1310222.4303973
timestamps[0] 1310223.4447196
timestamps[0] 1310224.4420128001
timestamps[0] 1310225.4407846
timestamps[0] 1310226.4503933
timestamps[0] 1310227.4499237002
timestamps[0] 1310228.4625242
timestamps[0] 1310229.4636662
timestamps[0] 1310230.469094
event added: 1310232.4105778 2
timestamps[0] 1310231.4671544002

why events are not aligned with timestamps?


Connected to BioSemi at 2048.0 Hz
timestamps[0] 10222.6520943375
timestamps[0] 10223.14594625
timestamps[0] 10223.6574869375
timestamps[0] 10224.14885540625
event added: 1312019.4391438 4
timestamps[0] 10225.155465862501
timestamps[0] 10225.652284875001
timestamps[0] 10226.1441703625
timestamps[0] 10227.1501757
timestamps[0] 10227.663202687501
timestamps[0] 10228.1591755
timestamps[0] 10229.162548856251
timestamps[0] 10229.652407425001
timestamps[0] 10230.1472325125
timestamps[0] 10231.16002099375
timestamps[0] 10231.6541061
timestamps[0] 10232.14583204375
timestamps[0] 10233.15566735625
timestamps[0] 10233.6460549
timestamps[0] 10234.15534974375
event added: 1312029.4412221 5
timestamps[0] 10235.160034556251
timestamps[0] 10235.653616825
timestamps[0] 10236.1637147125
timestamps[0] 10237.15564996875
timestamps[0] 10237.6512256375

in biosemi it seems like timestamps come from source PC instead of receiver



Connected to MockEEG at 250.0 Hz
timestamps[0] 1313019.1402902
timestamps[0] 1313020.105587
event added: 1313021.5634596501 2
timestamps[0] 1313021.1019506
timestamps[0] 1313022.1207142
timestamps[0] 1313023.1239039002
timestamps[0] 1313024.1258336
timestamps[0] 1313025.1406167
timestamps[0] 1313026.1456009
timestamps[0] 1313027.1468413002
timestamps[0] 1313028.1503064001
timestamps[0] 1313029.1532869001
event added: 1313030.94602205 4
timestamps[0] 1313030.1554607002
timestamps[0] 1313031.1628824
timestamps[0] 1313032.1685981

after adding self.lsl_offset to event timestamp, i thought it would be aligned, but now it's a bit off to the other side

////

onnected to MockEEG at 250.0 Hz
timestamps[0] 1313431.4616718001
timestamps[-1] 1313432.4441505
timestamps[0] 1313432.446917
timestamps[-1] 1313433.443362
event added: 1313433.7512941 4
timestamps[0] 1313433.4457635002
timestamps[-1] 1313434.4456624
timestamps[0] 1313434.4525128
timestamps[-1] 1313435.4602717
timestamps[0] 1313435.4624796
timestamps[-1] 1313436.4603157
timestamps[0] 1313436.4638707
timestamps[-1] 1313437.4738907
timestamps[0] 1313437.4803492
timestamps[-1] 1313438.4786163
timestamps[0] 1313438.4811902002
timestamps[-1] 1313439.4822843
timestamps[0] 1313439.4887535
timestamps[-1] 1313440.4910345
timestamps[0] 1313440.4935345
timestamps[-1] 1313441.4962902
timestamps[0] 1313441.4987338001
timestamps[-1] 1313442.4898544
event added: 1313443.1136478 1
timestamps[0] 1313442.4964504
timestamps[-1] 1313443.492811
timestamps[0] 1313443.4955158

looks better now: it's between first and last timestamp of next data chunk
lets see what happens with biosemi

////
Connected to BioSemi at 2048.0 Hz
timestamps[0] 11926.49521365625
timestamps[-1] 11926.98680834375
timestamps[0] 11926.987296625
timestamps[-1] 11927.99917273125
timestamps[0] 11927.9996610125
timestamps[-1] 11928.485488275
timestamps[0] 11928.48597655625
timestamps[-1] 11928.9956128625
event added: 2615517.1039116504 3
timestamps[0] 11928.99610114375
timestamps[-1] 11929.98789613125

oof, looks like i did it the wrong way

Connected to BioSemi at 2048.0 Hz
timestamps[0] 12042.5975384375
timestamps[-1] 12043.09376076875
timestamps[0] 12043.09424905
timestamps[-1] 12043.58943525625
timestamps[0] 12043.5899235375
timestamps[-1] 12044.5951927125
event added: 12045.147319700103 4
timestamps[0] 12044.59568099375
timestamps[-1] 12045.08771978125
timestamps[0] 12045.0882080625
timestamps[-1] 12045.58411499375
timestamps[0] 12045.584603275
timestamps[-1] 12047.0824811125
timestamps[0] 12047.08296939375
timestamps[-1] 12047.5946828
timestamps[0] 12047.5922457375
timestamps[-1] 12049.085405631251
timestamps[0] 12049.085893912501
timestamps[-1] 12049.596354175
timestamps[0] 12049.59684245625
timestamps[-1] 12051.09178108125
timestamps[0] 12051.0922693625
timestamps[-1] 12051.58368635
timestamps[0] 12051.58417463125
timestamps[-1] 12053.084260218751
event added: 12053.18962979992 1
timestamps[0] 12053.084748500001
timestamps[-1] 12053.59742330625
timestamps[0] 12053.5979115875
timestamps[-1] 12055.098866675
timestamps[0] 12055.09935495625
timestamps[-1] 12055.59125444375
timestamps[0] 12055.591742725
timestamps[-1] 12057.0926857875
timestamps[0] 12057.09317406875
timestamps[-1] 12057.5901255
timestamps[0] 12057.5882489375
timestamps[-1] 12058.08489596875
timestamps[0] 12058.08538425
timestamps[-1] 12059.089307525
timestamps[0] 12059.08979580625
timestamps[-1] 12059.5842409125
timestamps[0] 12059.58472919375
timestamps[-1] 12061.08667328125
timestamps[0] 12061.0871615625
timestamps[-1] 12061.57962236875
timestamps[0] 12061.58011065
timestamps[-1] 12063.09818204375
event added: 12063.2163497 2
timestamps[0] 12063.098670325
timestamps[-1] 12063.5896242875
timestamps[0] 12063.59011256875
timestamps[-1] 12064.081573931251
timestamps[0] 12064.082062212501
timestamps[-1] 12065.091747325001
timestamps[0] 12065.092235606251
timestamps[-1] 12065.5863278125
timestamps[0] 12065.58681609375
timestamps[-1] 12067.0866912375
timestamps[0] 12067.08717951875
timestamps[-1] 12067.58370425
timestamps[0] 12067.58419253125
timestamps[-1] 12069.096765875
timestamps[0] 12069.09725415625
timestamps[-1] 12069.5866304625
timestamps[0] 12069.58711874375
timestamps[-1] 12070.082259375
timestamps[0] 12070.08274765625
timestamps[-1] 12071.086194431251
timestamps[0] 12071.086682712501
timestamps[-1] 12071.5800583
timestamps[0] 12071.58054658125
timestamps[-1] 12073.09029796875
event added: 12073.226862499956 5
timestamps[0] 12073.09078625

looks a lot better, but still i'm unsure how I should do it

Connected to MockEEG at 250.0 Hz
timestamps[0] 1314023.1029214
timestamps[-1] 1314024.0874728
timestamps[0] 1314024.0899604
timestamps[-1] 1314025.0862867
event added: 1314025.3443957001 2
timestamps[0] 1314025.0925763
timestamps[-1] 1314026.090357
timestamps[0] 1314026.0966313
timestamps[-1] 1314027.0947758
timestamps[0] 1314027.0973089
timestamps[-1] 1314028.0899522
timestamps[0] 1314028.0963949
timestamps[-1] 1314029.1092636
timestamps[0] 1314029.1155734
timestamps[-1] 1314030.1056601
timestamps[0] 1314030.1119281
timestamps[-1] 1314031.1194415
timestamps[0] 1314031.1218085
timestamps[-1] 1314032.112299
timestamps[0] 1314032.1149369
timestamps[-1] 1314033.1258739
event added: 1314033.7566026 5
timestamps[0] 1314033.1323267
timestamps[-1] 1314034.1177492

In mocklsl looks good, now let's try to measure if it's saved correctly
Maybe basing on mock signal we could measure event is good place
data would rise each sample so if we know what frequency it is, we could caluclate when event should be added
    preparation_duration: float = 1.0
    recording_duration: float = 5.0
so with 250Hz it should be 250 samples for preparation and 1250 for recording
event should happen at 1.0 second = 250 
but it happened at 2.81 seconds ?? maybe its due to existing data in ring as we don't know when it started (its running in background)
Best i can do is to try recording with biosemi and touch electrode on event and see how it does look in file

there was some strange signal every 100-200 ms (very high voltage) ant it was caused by amplifier: it check if CMS/DRL is alright to prevent damage with applying too much voltage and then it cuts off itself. 
To mitigate this I needed to connect DRL/CMS to some ground: I put it in the water and then "CM in range" light was light (not blinking as before)
