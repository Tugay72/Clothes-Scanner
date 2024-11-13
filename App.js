import { StatusBar } from 'expo-status-bar';
import React, {useState, useRef, useEffect} from 'react';
import axios from 'axios';

import { StyleSheet, Text, TouchableOpacity, View, Image, Alert } from 'react-native';
import { CameraView, useCameraPermissions, useMicrophonePermissions } from 'expo-camera';
import * as MediaLibrary from 'expo-media-library';

import CameraButton from './frontend/components/camera_button'

export default function App() {

  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [microphonePermission, requestMicrophonePermission] = useMicrophonePermissions();
  const [mediaLibraryPermision, requestMediaLibraryPermission] = MediaLibrary.usePermissions();
  const [cameraProps, setCameraProps] = useState({
    zoom: 0,
    facing : 'front',
    flash: 'on',
    animateShutter: false,
    enableTorch: false
  })
  const [image, setImage] = useState(null);
  const [processedImage, setProcessedImage] = useState(null); // Store processed image
  const [previousImage, setPreviousImage] = useState(null);

  const cameraRef = useRef(null);

  const [colorData, setColorData] = useState(null);

  // Load the last saved image after permision change
  useEffect(() => {
    if (cameraPermission && cameraPermission.granted &&
       mediaLibraryPermision && mediaLibraryPermision.status === 'granted' &&
       microphonePermission && microphonePermission.granted) {
        getLastSavedImage();
    }
  },  [cameraPermission, mediaLibraryPermision])

  if(!cameraPermission || !mediaLibraryPermision){
    //permission are still loading
    return (
      <View style = {styles.container}>
        <Text>Permissions are loading...</Text>
      </View>
    );
  }

  if (!cameraPermission.granted || mediaLibraryPermision.status !== 'granted' || !microphonePermission.granted){
    //permissions are not granted yet
    return (
      <View style = {styles.permissionContainer}>
        <Text>We need your permission to continue</Text>
        <TouchableOpacity 
          style = {styles.permissionButton}
          onPress={() => {
            requestCameraPermission();
            requestMediaLibraryPermission();
            requestMicrophonePermission();
          }}
        >
          <Text style = {styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
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
  const takePicture = async() => {
    if(cameraRef.current) {
      try{
        const picture = await cameraRef.current.takePictureAsync();
        setImage(picture.uri);
      } catch (err) {
        console.log('Error while taking picture!', err)
      }
    }
  }

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
  const processImage = async () => {
    if (image) {
      try {
        const formData = new FormData();
        formData.append('image', {
          uri: image, // The URI of the image
          type: 'image/jpeg', // Image type
          name: 'photo.jpg', // A name for the file
        });
        //10.40.126.42:5000 okul agi
        const response = await axios.post('http://192.168.1.110:5000/process-image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data', // Content type: multipart/form-data
          },
        });
  
        console.log(response);
        const { average_color, average_color_name } = response.data;

        // Show an alert with color details
        Alert.alert(
          "Color Analysis",
          `Average Color: ${average_color_name}\nRGB: ${average_color}`,
          [
            {
              text: "OK",
              style: "default"
            }
          ]
        );
        
        setProcessedImage(response.data.processed_image);
      } catch (err) {
        console.error('Error processing image:', err);
        Alert.alert('Processing Error', 'There was an issue processing the image.');
      }
    }
  };

  return (
    <View style={styles.container}>
      {!image ? (
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
            <TouchableOpacity onPress={() => previousImage && setImage(previousImage)}>

              <Image 
                source={{uri:previousImage}}
                style={styles.previousImage}
              />
            </TouchableOpacity>
            <CameraButton
              icon = 'circle'
              size = {60}
              style={{height: 60}}
              onPress = {takePicture}
            />
            <CameraButton 
              icon = 'flip-camera-ios'
              size={40}
              style={{height: 60}}
              onPress={() => toggleProperty('facing', 'front', 'back')}
            />
          </View>
        </>
      ) : (
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
      )}
      
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
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
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
    width: '100%'
  },

  bottomControlsContainer: {
    height: 120,
    padding: 20,
    backgroundColor: 'black',
    flexDirection: 'row',
    justifyContent: 'space-around',
  },

  permissionButton: {
    backgroundColor: 'blue',
    padding: 10,
    margin: 10,
    borderRadius: 2
  },

  permissionButtonText: {
    color : 'white',
    fontSize: 16
  },

  previousImage: {
    marginTop: 5,
    width: 50,
    height: 50,
    borderRadius: 30
  }
});
