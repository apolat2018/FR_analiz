# -*- #################
#Ali POLAT
#ANALÝZ ve TEST HEYELANLARIný BÝZ BELÝRLEDÝK
import arcpy, os
from arcpy.sa import *
arcpy.env.overwriteOutput = True
#...........................Parametreler.................
rec=arcpy.GetParameterAsText(0)
analiz_hey=arcpy.GetParameterAsText(1)
test_hey=arcpy.GetParameterAsText(2)
#---------------------------------------
arcpy.env.workspace=rec
rec_list=arcpy.ListDatasets("rec*","raster")
arcpy.AddMessage(rec_list)
ext_file=rec_list[0]
ext=os.path.join(rec,ext_file)
arcpy.env.extent=ext
##split heyelan

##arcpy.AddMessage("analiz ve test heyelanlari seciliyor")
##test_hey=os.path.join(rec,str("test_hey.shp"))
##analiz_hey=os.path.join(rec,str("analiz_hey.shp"))
##arcpy.AddField_management(hey,"sec","SHORT")
##arcpy.CalculateField_management(hey,"sec",'math.fmod(!FID!,5)',"PYTHON")
##arcpy.Select_analysis(hey,test_hey,"sec=1")
##arcpy.Select_analysis(hey,analiz_hey,"sec<>1")
#parametrelerin heyelanli pikselleri belirleniyor

arcpy.AddMessage("Heyelanli pikseller belirleniyor")
for i in rec_list:
    masking=ExtractByMask(i,analiz_hey)
    mask_out = os.path.join(rec,str("hey_"+(i)))
    masking.save(mask_out)
    arcpy.AddMessage(i+"_icin islem devam ediyor")



for n in rec_list:
    d=[]
    fields0= [c.name for c in arcpy.ListFields(n) if not c.required]
    arcpy.AddMessage(fields0)
    for k in fields0:
        if k=="VALUE" or k=="COUNT" :
            d.append(k)
            arcpy.AddMessage("k="+k)
        else:
            arcpy.AddMessage("k value yada count deðil")
            pass
        
    if len(fields0)>2 and len(d)==2:
        fields0.remove(d[0])
        fields0.remove(d[1])
        arcpy.DeleteField_management(n,fields0)
    arcpy.AddMessage(n+"Fields_Silindi.......")
    

##-Analiz Hesaplamalari Yapýlýyor-------------------------
hey_list=arcpy.ListDatasets("hey_rec*","Raster")
for j,k in zip(rec_list,hey_list):
    arcpy.JoinField_management(j,"Value",k,"Value","count")
lst=[]
lst2=[]
lstmax=[]
top_pix_field="count","hp"
fieldTpx=['sumtpx','sumlpx']
for l in rec_list:
    outname =str("tablo"+(l)+".dbf")
    outname_table=os.path.join(rec,outname)
    outname_to_sus=os.path.join(rec,str("ts"+(l)))
    arcpy.AddField_management(l,"hp","DOUBLE")
    arcpy.AddField_management(l,"sumtpx","DOUBLE")
    arcpy.AddField_management(l,"sumlpx","DOUBLE")
    arcpy.AddField_management(l,"max","DOUBLE")
    arcpy.AddField_management(l,"fr","DOUBLE")
    arcpy.AddField_management(l,"nfr","SHORT")
    arcpy.CalculateField_management(l,"hp","!count_1!","PYTHON")
    with arcpy.da.UpdateCursor(l,"hp") as upcursor:
        for row in upcursor:
            if row[0]== None:
                row[0]=0
                upcursor.updateRow(row)
            del row
        del upcursor    
    with arcpy.da.SearchCursor(l,top_pix_field) as cursor:
        sum_tpx=0
        sum_lpx=0
        for row1 in cursor:
            sum_tpx +=row1[0]
            sum_lpx +=row1[1]
        lst.append(sum_tpx)
        lst2.append(sum_lpx)
        del row1
    del cursor  
    with arcpy.da.UpdateCursor(l,fieldTpx) as upcursor2:
        for row2 in upcursor2:
            row2[0]=lst[-1]
            row2[1]=lst2[-1]
            upcursor2.updateRow(row2)
            del row2
        del upcursor2  
    arcpy.CalculateField_management(l,"fr","(!hp!/!sumlpx!)/(!count!/!sumtpx!)","PYTHON")
    maximum = max(row3[0] for row3 in arcpy.da.SearchCursor(l, ['fr']))
    with arcpy.da.SearchCursor(l,"fr") as cursor2:
        for row3 in cursor2:
            lstmax.append(row3[0])
            maxfr=max(lstmax)
            del row3
        del cursor2  
    with arcpy.da.UpdateCursor(l,"max") as upcursor3:
        for row4 in upcursor3:
            row4[0]=maximum
            upcursor3.updateRow(row4)
            del row4
        del upcursor3  
    arcpy.CalculateField_management(l,"nfr","(!fr!/!max!*100)","PYTHON")

    
    
    arcpy.TableToTable_conversion(l,rec,outname)

    to_sus=ReclassByTable(l,outname_table,"VALUE","VALUE","nfr","NODATA")
    to_sus.save(outname_to_sus)
###------------------------------------RASTER CALCULATER ILE RASTERLAR TOPLANIYOR--------
duy_lst=arcpy.ListDatasets("ts*","Raster")
sus_map=arcpy.sa.CellStatistics(duy_lst,"SUM","DATA")
sus_map_name=os.path.join(rec,str("sus_map"))
sus_map.save(sus_map_name)
arcpy.AddMessage("Duyarlilik haritasý tamam")
###------------------------------SUS_MAP RECLASS YAPILIYOR_ PERFORMANS HESAPLANIYOR------
sus_map_table_name="sus_table.dbf"
rcv=[] 
upfields="value","sinif"
sus_table_dir=os.path.join(rec,sus_map_table_name)
arcpy.TableToTable_conversion(sus_map_name,rec,sus_map_table_name)
with arcpy.da.SearchCursor(sus_table_dir,"value") as cursor3:
    for row5 in cursor3:
        rcv.append(row5[0])
print(rcv)
mx=rcv[-1]
mn=rcv[0]
ara=(mx-mn)/5
x=mn+4*ara
print(mn)
print(ara)
sus_map_table_dir=os.path.join(sus_map_name,rec,sus_map_table_name)
arcpy.AddField_management(sus_map_table_dir,"sinif","SHORT")
with arcpy.da.UpdateCursor(sus_map_table_dir,upfields) as upcur4:
    for row6 in upcur4:
        if row6[0] >=0 and row6[0]<=mn+ara:
            row6[1]=1
        elif row6[0] >=mn+ara and row6[0]<=mn+2*ara:
            row6[1]=2
        elif row6[0] >=mn+2*ara and row6[0]<=mn+3*ara:
            row6[1]=3
        elif row6[0] >=mn+3*ara and row6[0]<=mn+4*ara:
            row6[1]=4
        elif row6[0] >=mn+4*ara:
            row6[1]=5
        upcur4.updateRow(row6)

rec_sus=ReclassByTable(sus_map_name,sus_map_table_dir,"value","value","sinif","NODATA")
rec_sus_dir=os.path.join(rec,str("rec_sus"))
rec_sus.save(rec_sus_dir)
arcpy.AddMessage("duyarlilik haritasinin reclass islemi tamam")
##-------------------------------------PERFORMANS HESAPLANIYOR-----------------
performans=ExtractByMask(rec_sus_dir,test_hey)
performans_dir=os.path.join(rec,str("performans"))
performans.save(performans_dir)


arcpy.AddField_management(performans_dir,"dortbes","DOUBLE")
arcpy.AddField_management(performans_dir,"per","DOUBLE")
per_fields="value","count","dortbes","per"



lst3=[]
lst4=[]
with arcpy.da.UpdateCursor(performans_dir,per_fields) as upcur5:
    for row7 in upcur5:
        if row7[2]==None:
            row7[2]=0
        elif row7[3]==None:
            row7[3]=0
        
        arcpy.AddMessage("Bitmek uzere")
        if row7[0]==4:
            row7[2]=row7[1]
        elif row7[0]==5:
            row7[2]=row7[1]
        elif row7[0]==1 or row7[0]==2 or row7[0]==3:
            row7[2]=0
        
        upcur5.updateRow(row7)
with arcpy.da.SearchCursor(performans_dir,per_fields) as cursor4:
    for row8 in cursor4:
        lst3.append(row8[1])
        lst4.append(row8[2])
toplam=sum(lst3)
t45=sum(lst4)
per=t45/toplam*100
with arcpy.da.UpdateCursor(performans_dir,per_fields) as upcur6:
    for row9 in upcur6:
        row9[3]=per
        upcur6.updateRow(row9)



arcpy.AddMessage("Analiz Performansý= "+str(per))





