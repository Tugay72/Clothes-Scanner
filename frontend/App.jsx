import React, {useState, useRef, useEffect} from 'react';
import { StyleSheet, Text, TouchableOpacity, View, Image, Alert } from 'react-native';
import * as Animatable from 'react-native-animatable';

import axios from 'axios';

import * as MediaLibrary from 'expo-media-library';
import { StatusBar } from 'expo-status-bar';
import { CameraView, useCameraPermissions, useMicrophonePermissions } from 'expo-camera';
import * as Speech from 'expo-speech';

import CameraButton from './components/camera_button'

import translate from 'translate';
import tr_dict from './turkish_localization';
translate.engine = 'google';

export default function App() {
  
  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [microphonePermission, requestMicrophonePermission] = useMicrophonePermissions();
  const [mediaLibraryPermision, requestMediaLibraryPermission] = MediaLibrary.usePermissions();
  const [cameraProps, setCameraProps] = useState({
    zoom: 0,
    facing : 'back',
    flash: 'off',
    animateShutter: false,
    enableTorch: false
  })
  const [image, setImage] = useState(null);
  const [processedImage, setProcessedImage] = useState(null);
  const [previousImage, setPreviousImage] = useState(null);

  const cameraRef = useRef(null);

  const [colorData, setColorData] = useState(null);
  const [showIntro, setShowIntro] = useState(true);


  // Load the last saved image after permision change
  // useEffect(() => {
  //   if (cameraPermission && cameraPermission.granted &&
  //      mediaLibraryPermision && mediaLibraryPermision.status === 'granted' &&
  //      microphonePermission && microphonePermission.granted) {
  //       getLastSavedImage();
  //   }
  // },  [cameraPermission, mediaLibraryPermision])

  useEffect(() => {
    const handleIntroAndPermissions = async () => {
      // Simulate animation duration
      await new Promise(resolve => setTimeout(resolve, 3000)); // 3-second intro

      // Request permissions
      await requestCameraPermission();
      await requestMediaLibraryPermission();
      await requestMicrophonePermission();

      // Update state
      setShowIntro(false);
      
    };

    handleIntroAndPermissions();
  }, []);

  if (showIntro) {
    // Show animated intro
    return (
      <View style={styles.permissionContainer}>
        <Animatable.Image animation="fadeIn" iterationCount={1}></Animatable.Image>
          <Image source={require('./assets/logo.png')} style={styles.introLogo}/>
      </View>
    );
  }

  if(!cameraPermission || !mediaLibraryPermision || !microphonePermission){
    //Permission are still loading
    return (
      <View style = {styles.permissionContainer}>
        <Text>Permissions are loading...</Text>
      </View>
    );
  }

  // Permissions not granted yet
  if (!cameraPermission.granted || mediaLibraryPermision.status !== 'granted' || !microphonePermission.granted) {
    // Permissions are not granted yet
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          Please grant all permissions to proceed.
        </Text>
      </View>
    );
  }

  // Function to toggle camera props
  const toggleProperty = (prop, option1, option2) => {
    setCameraProps((current) =>({
      ...current,
      [prop]:current[prop] === option1 ? option2 : option1
    }))
  }

  // Take pictures
  const takePicture = async () => {
    if (cameraRef.current) {
      try {
        const picture = await cameraRef.current.takePictureAsync();
        console.log("Picture URI:", picture.uri); // Debugging için URI'yi yazdır
        setImage(picture.uri);
        
        // Görüntüyü işleme gönder
        processImage(picture.uri); // Fonksiyona URI gönderiyoruz
      } catch (err) {
        console.log("Error while taking picture!", err);
        Speech.speak('Fotoğraf çekerken bir hata oluştu', {
          language: "tr-TR",
        });
      }
    }
  };

  // Save taken pictures
  const savePicture = async() => {
    if (image) {
      try{
        processImage();

        const asset = await MediaLibrary.createAssetAsync(image);
        const assetInfo = await MediaLibrary.getAssetInfoAsync(asset.id);
        Alert.alert('Photo saved!', `Image URI: ${image}`);
        setImage(null);
        getLastSavedImage();
        
      }catch (err) {
        console.log('Error while saving the picture : ', err);
      }
    }
  }

  //Get previous taken picture from 'DCIM' album created by expo if doesnt exist
  const getLastSavedImage = async() => {
    if(mediaLibraryPermision && mediaLibraryPermision.status === 'granted') {
      const dcimAlbum = await MediaLibrary.getAlbumAsync('DCIM');

      if (dcimAlbum) {
        const {assets} = await MediaLibrary.getAssetsAsync({
          album : dcimAlbum,
          sortBy: [(MediaLibrary.SortBy.creationTime, MediaLibrary.SortBy.default)],
          mediaType: MediaLibrary.MediaType.photo,
          first: 1
        });

        if (assets.length > 0) {
          const assetInfo = await MediaLibrary.getAssetInfoAsync(assets[0].id);
          setPreviousImage(assetInfo.localUri || assetInfo.uri);
        }
        else{
          setPreviousImage(null);
        }
      }
      else{
        setPreviousImage(null);
      }
    }
  }

  // Send image to Flask API for processing
  const processImage = async (imageUri) => {
    if (imageUri) {
      try {
        const formData = new FormData();
        formData.append("image", {
          uri: imageUri,
          type: "image/jpeg",
          name: "photo.jpg",
        });
  
        const response = await axios.post("http://192.168.1.112:5000/process-image", formData, {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        });
  
        console.log("Response from API:", response.data);
        const {
          average_color,
          average_color_name,
          dominant_color,
          dominant_color_name,
          pattern,
          pattern_confidence,
        } = response.data;
  
        // Speak and display processed data
        // const mergedString = `
        //   The dominant color of the clothing is: (${average_color_name}), 
        //   while the average color is : (${dominant_color_name}). 
        //   The pattern of the clothing is : ${pattern},
        //   with the confidence of (${pattern_confidence}%)
        //   `.trim();

        // const mergedString2 = `
        //   Average Color: (${average_color_name}),
        //   Dominant Color: (${dominant_color_name}),
        //   Pattern: ${pattern} (Confidence: ${pattern_confidence}%)
        // `.trim();

        const translated_average_color_name = tr_dict[average_color_name.toString()];
        const translated_pattern = tr_dict[pattern.toString()];
        let turkishString = ``;

        if (dominant_color_name.split(",").length > 1) {
          const colorsArray = dominant_color_name.split(/\s*,\s*/);
          let newColorsArray = '';
          for(const color of colorsArray){
            let translatedColor = tr_dict[color.toString()];
            newColorsArray += translatedColor + ' ve '
          }
          

          newColorsArray = newColorsArray.slice(0, -4);
          
          console.log(newColorsArray)

          turkishString = `
            Kıyafetin dominant renkleri ${newColorsArray}
            olmak üzere ortalama rengi: ${translated_average_color_name}. 
            Kıyafetin deseni ${pattern_confidence} doğruluk payı ile ${translated_pattern}.
          `.trim();

        } else {
          const translated_dominant_color_name = tr_dict[dominant_color_name.toString()];
          turkishString = `
            Kıyafetin dominant rengi: ${translated_dominant_color_name}
            olmak üzere ortalama rengi: ${translated_average_color_name}. 
            Kıyafetin deseni ${pattern_confidence} doğruluk payı ile ${translated_pattern}.
          `.trim();
        }


        // const turkishText = await translate(translatedString, { to: "tr" });
        // Speech.speak(turkishText, {
        //   language: "tr-TR",
        // });

        console.log(turkishString);
        Speech.speak(turkishString, {
          language: "tr-TR",
        });
  
        setProcessedImage(response.data.processed_image);
      } catch (err) {
        console.error("Error processing image:", err);
        Alert.alert("Processing Error", "There was an issue processing the image.");
      }
    }
  };
  

  return (
    <View style={styles.container}>
      {/* {!image ? ( */}
        <>
          <View style = {styles.topControlsContainer}>
            <CameraButton 
              icon = {cameraProps.flash === 'on' ? 'flash-on' : 'flash-off'}
              onPress={() => toggleProperty('flash', 'on', 'off')}
            />
            <CameraButton 
              icon = 'animation'
              color={cameraProps.animateShutter ? 'white' : '#404040'}
              onPress={() => toggleProperty('animateShutter', true, false)}
            />
            <CameraButton 
              icon = 'flashlight-on'
              color={cameraProps.enableTorch ? 'white' : '#404040'}
              onPress={() => toggleProperty('enableTorch', true, false)}
            />
          </View>
          <CameraView 
            style = {styles.camera}
            zoom = {cameraProps.zoom}
            facing = {cameraProps.facing}
            flash = {cameraProps.flash}
            animateShutter = {cameraProps.animateShutter}
            enableTorch = {cameraProps.enableTorch}
            ref={cameraRef}
          />

          <View style = {styles.bottomControlsContainer}>
            
            <CameraButton
              icon = 'circle'
              size = {90}
              style={{height: 90}}
              onPress = {takePicture}
            />
            
          </View>
        </>
      {/* ) : (
        <>
          <Image 
            source = {{uri:image}} 
            style = {styles.camera}/>

          <View style = {styles.bottomControlsContainer}>
            <CameraButton 
              icon = 'flip-camera-android'
              size = {40}
              onPress={() => setImage(null)}
            />
            <CameraButton 
              icon = 'check'
              size = {40}
              onPress={savePicture}
            />
          </View>
        </>
      )} */
      }
      
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },

  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },

  intro: {
    fontSize: 24,
    color: 'black',
    fontWeight: 'bold',
    textAlign: 'center',
  },

  introLogo: {
    width: 96,
    height: 52,
    marginBottom: 30,
  },

  topControlsContainer: {
    height: 100,
    paddingTop: 30,
    backgroundColor: 'black',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center'
  },

  camera: {
    flex: 1,
    width: '100%',
    height: '100%',
  },

  bottomControlsContainer: {
    height: 150,
    paddingBottom: 30,
    backgroundColor: 'black',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },

  previousImage: {
    marginTop: 5,
    width: 50,
    height: 50,
    borderRadius: 30
  }
});

