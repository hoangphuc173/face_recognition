import React, { useState, useEffect } from 'react';
import * as faceapi from 'face-api.js';

interface Person {
  id: number;
  name: string;
  image_url: string;
}

// Helper function to convert file to base64
const toBase64 = (file: File): Promise<string> => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = error => reject(error);
});

const People = () => {
  const [people, setPeople] = useState<Person[]>([]);
  const [newPersonName, setNewPersonName] = useState('');
  const [newPersonImage, setNewPersonImage] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    const loadModels = async () => {
      const MODEL_URL = '/models';
      try {
        await Promise.all([
          faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
          faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
          faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
        ]);
        setModelsLoaded(true);
        console.log('Face-api models loaded for People component');
      } catch (error) {
        console.error('Error loading face-api models:', error);
        alert('Failed to load face recognition models. Please refresh the page.');
      }
    };
    loadModels();
  }, []);

  useEffect(() => {
    const fetchPeople = async () => {
      try {
        // TODO: Implement API call to get people from backend
        // const response = await fetch('http://127.0.0.1:8888/api/people');
        // const result: Person[] = await response.json();
        const result: Person[] = [];
        setPeople(result);
      } catch (error) {
        console.error('Error fetching people:', error);
        alert('Failed to load people from the backend.');
      } finally {
        setLoading(false);
      }
    };

    fetchPeople();
  }, []);

  const handleAddPerson = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newPersonName || !newPersonImage) {
      alert('Please provide a name and an image.');
      return;
    }
    if (!modelsLoaded) {
        alert('Models are still loading, please wait.');
        return;
    }

    setIsProcessing(true);

    try {
      const image = await faceapi.bufferToImage(newPersonImage);
      const detection = await faceapi
        .detectSingleFace(image)
        .withFaceLandmarks()
        .withFaceDescriptor();

      if (!detection) {
        alert('No face detected in the image. Please use a clearer picture.');
        setIsProcessing(false);
        return;
      }

      const descriptor = Array.from(detection.descriptor);
      const imageUrl = await toBase64(newPersonImage);

      // TODO: Implement API call to add person
      // const response = await fetch('http://127.0.0.1:8888/api/people', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ name: newPersonName, imageUrl, descriptor })
      // });
      // const updatedPeople: Person[] = await response.json();
      const updatedPeople: Person[] = [...people, { id: Date.now(), name: newPersonName, image_url: imageUrl }];

      setPeople(updatedPeople);
      setNewPersonName('');
      setNewPersonImage(null);
      const fileInput = document.getElementById('imageUpload') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

    } catch (error) {
      console.error('Error adding person:', error);
      alert('Failed to add person. See console for details.');
    } finally {
        setIsProcessing(false);
    }
  };

  const handleDeletePerson = async (id: number) => {
    try {
      // TODO: Implement API call to delete person
      // await fetch(`http://127.0.0.1:8888/api/people/${id}`, { method: 'DELETE' });
      const updatedPeople: Person[] = people.filter(p => p.id !== id);
      setPeople(updatedPeople);
    } catch (error) {
      console.error('Error deleting person:', error);
      alert('Failed to delete person.');
    }
  };

  if (loading) {
    return <div>Loading people...</div>;
  }

  return (
    <div className="people-container">
      <h2>Manage People</h2>

      <div className="add-person-form">
        <h3>Add New Person</h3>
        <form onSubmit={handleAddPerson}>
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              value={newPersonName}
              onChange={(e) => setNewPersonName(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="imageUpload">Image</label>
            <input
              type="file"
              id="imageUpload"
              accept="image/*"
              onChange={(e) => e.target.files && setNewPersonImage(e.target.files[0])}
              required
            />
          </div>
          <button type="submit" disabled={!modelsLoaded || isProcessing}>
            {isProcessing ? 'Processing...' : (modelsLoaded ? 'Add Person' : 'Loading Models...')}
          </button>
        </form>
      </div>

      <div className="people-list">
        <h3>Existing People</h3>
        {people.length === 0 ? (
          <p>No people found. Add someone new!</p>
        ) : (
          <ul>
            {people.map((person) => (
              <li key={person.id}>
                <img src={person.image_url} alt={person.name} width="100" />
                <span>{person.name}</span>
                <button onClick={() => handleDeletePerson(person.id)}>Delete</button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default People;