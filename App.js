import { StatusBar } from 'expo-status-bar';
import React, {useState, useRef, useEffect} from 'react';

import { StyleSheet, Text, TouchableOpacity, View, Image } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';

import CameraButton from './frontend/components/camera_button'

export default function App() {

  const [cameraPermission, requestCameraPermission] = useCameraPermissions();
  const [cameraProps, setCameraProps] = useState({
    zoom: 0,
    facing : 'front',
    flash: 'on',
    animateShutter: false,
    enableTorch: false
  })
  const [image, setImage] = useState(null);
  const cameraRef = useRef(null);

  if(!cameraPermission){
    //permission are still loading
    return <View />
  }

  if (!cameraPermission.granted){
    //permissions are not granted yet
    return (
      <View>
        <Text>We need your permission to continue</Text>
        <TouchableOpacity>
          <Text>Grant Permission</Text>
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

  const savePicture = () => {
    console.log('a')
  }

  return (
    <View style={styles.container}>
      {!image ? (
        <>
          <View style = {styles.topControlsContainer}>
            <CameraButton 
              icon = 'flip-camera-ios'
              onPress={() => toggleProperty('facing', 'front', 'back')}
            />
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
              icon = 'camera'
              size = {60}
              style={{height: 60}}
              onPress = {takePicture}
            />
          </View>
        </>
      ) : (
        <>
          <Image source = {{uri:image}} style = {styles.camera}/>
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
  topControlsContainer: {
    height: 100,
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
    height: 100,
    padding: 10,
    backgroundColor: 'black',
    flexDirection: 'row',
    justifyContent: 'space-around',
  }
});
