import sys,subprocess,time
menus=[(2,"구례 대 화엄사","구례-대-화엄사"),(3,"해인사","해인사"),(4,"흑백마애불 암각화 봉정사 통도사","흑백마애불-암각화-봉정사-통도사"),(5,"운주사","운주사"),(6,"선암사","선암사"),(8,"MORE GALLERIES 판매작품","MORE-GALLERIES판매작품"),(9,"flower 연꽃사진","flower연꽃사진"),(11,"네팔 캄보디아 미얀마","네팔--캄보디아--미얀마"),(12,"風景 landscape","風景-landscape"),(13,"도서발간","도서발간")]
for i,d,p in menus:
    t=time.time()
    r=subprocess.run(['python3','menu.py',str(i),d,p],capture_output=True,text=True)
    print('###',i,d,round(time.time()-t),'s'); print(r.stdout[:700]); print(r.stderr[-300:],flush=True)
print('ALLDONE',flush=True)
