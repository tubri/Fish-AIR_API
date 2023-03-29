#!/bin/bash
# TULANE UNIVERSITY BIODIVERSITY RESEARCH INSTITUTE (TUBRI)
# baltintas@tulane.edu

#new_csv=$(paste -d ',' ./imageQualityMetadata.csv ./multimedia.csv ./extendedImageMetadata.csv > tmp.csv)
new_csv=$(cat ./multimedia.csv > tmp.csv)

echo "############ FISH-AIR AUTO IMAGE DOWNLOADER (TEST) ##############"
usage()
{
   echo ""
   echo "Usage: $0 -s FILTERINGFIELD -v KEYWORD -g GROUPINGFIELD"
   echo -e "\t-h  Shows this help "
   echo -e "\t-s name of the FILTERINGFIELD"
   echo -e "\t-v keyword for your filtering"
   echo -e "\t-g grouping parameter. Can be grouped(downloaded to corresponding folder) by GROUPINGFIELD"
   echo -e "\tExample: $0 -s \"genus\" -v \"Esox\" -g scientificName"
   echo -e "\tExample: $0 -s \"genus\" -v \"Esox\" "
   echo -e "\tor to download all: $0 " 
   
   
   
}

function ask_yes_or_no() {
    read -p "$1 ([y]es or [N]o): "
    case $(echo $REPLY | tr '[A-Z]' '[a-z]') in
        Y|y|yes) echo "" ;;
        N|n|no) echo "Canceled"; rm tmp.csv; exit ;;
        *)     ask_yes_or_no $1 ;;
    esac
}

#usage
IFS=',' read -a var < tmp.csv
echo -e
echo -e "############ FILTER LIST ###############"
printf "[%s]\n" "${var[@]}"
echo -e "#######################################"


filter() {
  	awk ' 
	NR==1 {
   	for (i=1;i<=NF;i++) {
      	if ($i==SEARCHHDR) {
         	srchfld=i;
      	}
      	if ($i==OUTHDR) {
        	 outfld=i;
      	}

   	}

   	#print $srchfld OFS $outfld
	}

	NR>1 && $srchfld ~ SEARCHVAL {
   	print $outfld
	}
	' SEARCHHDR="$1" SEARCHVAL="$2" OUTHDR="$3" FS=, OFS=, FPAT='([^,]*)|("[^"]+")' tmp.csv
	
	
	}

while getopts ":s:v:g:h:" option; do
  case "$option" in
    s)  SEARCHFIELD="$OPTARG" ;;
    v)  SEARCHVALUE="$OPTARG" ;;
    g)  GROUPBY="$OPTARG" ;;
    ?)  usage 
        
        exit 1
        ;;
  esac
done    

if [ -z ${SEARCHFIELD+x} ]; then
	echo "Filtering field is not available"
	
else
	echo -e "SEARCHFIELD: $SEARCHFIELD"

	if [ -z ${SEARCHVALUE+x} ]; then
		echo -e "You must enter the search value"
		SEARCHVALUE=""
		echo -e "..or you can  download all images"
		ask_yes_or_no "Continue downloading"
	else
        	
        	echo -e "SEARCHVALUE: $SEARCHVALUE"
 	fi
fi

if [ -z ${GROUPBY+x} ]; then
	echo "NO GROUPING"
	GROUPBY=""
else
	echo -e "GROUPBY: $GROUPBY"
fi

#SEARCHFIELD="nonSpecimenObjects"
#SEARCHVALUE="string, tag"
declare -i fileOK
if [ ! -z ${SEARCHFIELD+x} ] && [[ ! -z $(printf '%s\n' "${var[@]}" | grep -w $SEARCHFIELD) ]]; then
    
	RESULTFIELD="accessURI"
	
	results=$(filter $SEARCHFIELD "${SEARCHVALUE[@]}" $RESULTFIELD)

    ################### 
	
	echo -e "Download starting..."

	###################

else
	
	SEARCHFIELD="ARKID"
	SEARCHVALUE=""
	RESULTFIELD="accessURI"
	results=$(filter $SEARCHFIELD "${SEARCHVALUE[@]}" $RESULTFIELD)

	echo -e "########## URL LIST ################"
	n=1
	while IFS= read -r line
		do
			echo -e $n" : $line"
			n=$(($n + 1))
	done <<< "$results"
	echo "Your filtering field is not available, downloading all"
	ask_yes_or_no "Continue"



	echo -e "Download starting..."

    sleep 2

fi



if [ ! -z ${GROUPBY+x} ] && [[ ! -z $(printf '%s\n' "${var[@]}" | grep -w $GROUPBY) ]]; then

	###################
	n=1
    fileOK=0	
	while IFS= read -r line
		do

		   SEARCHFIELD="accessURI" 
		   #echo $SEARCHFIELD $line $GROUPBY
	       copydir=$(filter $SEARCHFIELD $line $GROUPBY)
	       copydir=${copydir//[[:blank:]]/_}
	       copydir=${copydir//\"/}
		   
		   if [[ $fileOK -ne 1 ]]; 
		   then

	       mkdir -p "images/$GROUPBY"
		   touch  "images/$GROUPBY/upload_image.csv"
	       truncate -s 0 "images/$GROUPBY/upload_image.csv"
	       touch  "images/$GROUPBY/url_list.txt"
	       truncate -s 0 "images/$GROUPBY/url_list.txt"
	       touch  "images/$GROUPBY/file_paths.txt"
	       truncate -s 0 "images/$GROUPBY/file_paths.txt"	       
	       echo "parentARKID,imageLocalPath,scientificName,genus,family,license,source,ownerInstitutionCode"   >> "images/$GROUPBY/upload_image.csv"
	       fileOK=1
	      
	       fi
	       wget -N $line -P images/$GROUPBY/$copydir
	       fileName=$(basename $line)
		   ARKID=${fileName%.*} # this becomes parentARKID
		   imageLocalPath=$(pwd)"/images/$GROUPBY/$copydir/$fileName"
		   scientificName=$(filter ARKID $ARKID scientificName)
		   genus=$(filter ARKID $ARKID genus)
		   family=$(filter ARKID $ARKID family)
		   license=$(filter ARKID $ARKID license)
		   source=$(filter ARKID $ARKID source)
		   ownerInstitutionCode=$(filter ARKID $ARKID ownerInstitutionCode)
		   echo "$ARKID,$imageLocalPath,$scientificName,$genus,$family,$license,$source,$ownerInstitutionCode" >> "images/$GROUPBY/upload_image.csv"
		   echo $line >> "images/$GROUPBY/url_list.txt"
		   echo $imageLocalPath >> "images/$GROUPBY/file_paths.txt"
	done <<< $results
	echo -e "#######################################"
    echo -e "Your files are downloaded to -> "$(pwd)"/images/$GROUPBY/"
    echo -e "#######################################"

	###################

else
	echo -e "Your grouping criteria is not available, downloading all..."
	n=1
	fileOK=0
	while IFS= read -r line
		do
		
		if [[ $fileOK -ne 1 ]];  then
			echo "Entered"
		    mkdir -p "images/all"
			touch  "images/all/upload_image.csv"
			truncate -s 0 "images/all/upload_image.csv"
			touch  "images/all/url_list.txt"
	        truncate -s 0 "images/all/url_list.txt"
	        touch  "images/all/file_paths.txt"
	        truncate -s 0 "images/all/file_paths.txt"
			echo "parentARKID,imageLocalPath,scientificName,genus,family,license,source,ownerInstitutionCode"  >> "images/all/upload_image.csv"
			fileOK=1
	   
	    fi
		wget -N $line -P images/all/
		fileName=$(basename $line)
		ARKID=${fileName%.*} # this becomes parentARKID
		imageLocalPath=$(pwd)"/images/all/$fileName"
		scientificName=$(filter ARKID $ARKID scientificName)
		genus=$(filter ARKID $ARKID genus)
		family=$(filter ARKID $ARKID family)
		license=$(filter ARKID $ARKID license)
		source=$(filter ARKID $ARKID source)
		ownerInstitutionCode=$(filter ARKID $ARKID ownerInstitutionCode)
		echo "$ARKID,$imageLocalPath,$scientificName,$genus,$family,$license,$source,$ownerInstitutionCode" >> "images/all/upload_image.csv"
		echo $line >> "images/all/url_list.txt"
		echo $imageLocalPath >> "images/all/file_paths.txt"

    	done <<< $results
	echo -e "#######################################"
    echo -e "Your files are downloaded to -> "$(pwd)"/images/all/"
    echo -e "#######################################"

fi

rm tmp.csv
exit 0



