import { Link } from 'react-router-dom';
import React, { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

export default function ExperienceUploadPage() {
  const [text, setText] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const handleTextChange = (e) => setText(e.target.value);
  const handleAudioChange = (e) => setAudioFile(e.target.files[0]);

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append('text', text);
    if (audioFile) {
      formData.append('audio', audioFile);
    }

    const response = await fetch('/api/experience-upload', {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      setSubmitted(true);
    } else {
      alert('There was a problem uploading your experience.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-stone-100 p-6 flex flex-col items-center">
      <Link
        to="/chat"
        className="text-amber-700 underline text-sm mb-4 hover:text-amber-900 self-start max-w-2xl"
      >
        🌊 Return to the River
      </Link>

      <Card className="w-full max-w-2xl bg-white/90 shadow-xl rounded-2xl">
        <CardContent className="p-6">
          <h1 className="text-2xl font-semibold mb-4 text-stone-800">
            🌿 Share Your Lahn River Experience
          </h1>
          <p className="mb-4 text-sm text-stone-600">
            Your voice helps shape the Lahn's avatar. Speak, write, or both — and help us understand how the river is experienced.
          </p>

          {!submitted ? (
            <>
              <div className="mb-4">
                <Label htmlFor="experience-text" className="text-stone-700">Your Message</Label>
                <Textarea
                  id="experience-text"
                  placeholder="Type your story or message here..."
                  value={text}
                  onChange={handleTextChange}
                  className="bg-white text-stone-800 border-stone-300"
                />
              </div>

              <div className="mb-4">
                <Label htmlFor="audio-upload" className="text-stone-700">Or upload a voice recording</Label>
                <Input
                  id="audio-upload"
                  type="file"
                  accept="audio/*"
                  onChange={handleAudioChange}
                  className="bg-white text-stone-800 border-stone-300"
                />
              </div>

              <Button className="bg-amber-600 text-white hover:bg-amber-700" onClick={handleSubmit}>
                Submit Experience
              </Button>
            </>
          ) : (
            <p className="text-green-700 font-semibold">🌱 Thank you for sharing your experience with the Lahn 💚</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
