import React from 'react';

const Camera: React.FC = () => {
  return (
    <div>
      <h2>Camera</h2>
      {/* Giao diện camera sẽ được thêm vào đây */}
      <video style={{ width: '100%', border: '1px solid black' }} autoPlay playsInline muted></video>
    </div>
  );
};

export default Camera;

