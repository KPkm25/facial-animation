import React, { Component } from "react";
import "./css/AudioRecorder.css";
import { Transition } from "react-transition-group";
import MediaStreamRecorder from 'msr'; // Import MediaStreamRecorder
import { transitionStyles, defaultStyle } from "../Config.js";

class AudioRecorder extends Component {
  constructor(props) {
    super(props);
    this.state = {
      recording: false,
      audioBlob: null,
      timer: "00:00",
    };
    this.mediaRecorder = null;
    this.timerInterval = null;
  }

  startRecording = () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        this.mediaRecorder = new MediaStreamRecorder(stream);
        this.mediaRecorder.mimeType = 'audio/wav'; // Set desired audio format
        this.mediaRecorder.ondataavailable = (blob) => {
          this.setState({ audioBlob: blob });
        };
        this.mediaRecorder.start(30000); // Start recording with a max duration of 30 seconds
        this.startTime = Date.now();
        this.timerInterval = setInterval(this.setTimer, 1000);
        this.setState({ recording: true });
      })
      .catch((error) => {
        console.error('Error accessing microphone:', error);
      });
  };

  setTimer = () => {
    const seconds = Math.floor((Date.now() - this.startTime) / 1000);
    const minutes = Math.floor(seconds / 60);
    const formattedSeconds = seconds < 10 ? `0${seconds}` : seconds;
    const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;
    this.setState({ timer: `${formattedMinutes}:${formattedSeconds}` });
  };

  stopRecording = () => {
    if (this.mediaRecorder) {
      this.mediaRecorder.stop();
      clearInterval(this.timerInterval);
      this.setState({ recording: false, timer: "00:00" });
    }
  };

  render() {
    return (
      <div id="recorder-container">
        <div className="horizontal-recorder">
          {!this.state.recording && (
            <button
              className="record-button record"
              onClick={this.startRecording}
              type="button"
            >
              Record
            </button>
          )}
          {this.state.recording && (
            <button
              className="record-button record"
              onClick={this.stopRecording}
              type="button"
            >
              Stop recording
            </button>
          )}
        </div>
        <Transition timeout={300} in={!!this.state.audioBlob}>
          {(state) => (
            <div style={{ ...defaultStyle, ...transitionStyles[state] }}>
              <a
                className="record download"
                href={this.state.audioBlob && URL.createObjectURL(this.state.audioBlob)}
                download="recording.wav"
              >
                Download
              </a>
            </div>
          )}
        </Transition>
      </div>
    );
  }
}

export default AudioRecorder;
