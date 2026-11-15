import React from 'react';
import {registerRoot,Composition} from 'remotion';
import {Film} from './Film';
registerRoot(()=> <Composition id="KStudioLaunch" component={Film} width={1920} height={1080} fps={30} durationInFrames={1800} defaultProps={{bgm:true}}/>);
