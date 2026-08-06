// src/components/TituloCard.jsx
import React from 'react';

const TituloCard = () => {
  return (
    <div className="w-full bg-pink-100 rounded-lg shadow flex items-center justify-between px-6 py-4 mb-8">
      <img
        src="/portada_tiendita_marian.jpeg"
        alt="Logo Marian"
        className="h-12 w-12 rounded-full object-cover"
      />
      <h1 className="text-2xl font-bold text-gray-800 tracking-tight">
        Tiendita de Marian
      </h1>
      <div className="w-12" /> {/* Espacio simétrico a la izquierda */}
    </div>
  );
};

export default TituloCard;
