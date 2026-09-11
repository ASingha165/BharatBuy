'use client';

import React from 'react';

interface BharatBuyLogoProps {
  className?: string;
  size?: number;
}

export const BharatBuyLogo: React.FC<BharatBuyLogoProps> = ({ className = '', size = 36 }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width={size}
      height={size}
      fill="none"
      className={className}
      aria-label="BharatBuy Logo"
    >
      <rect width="48" height="48" rx="10" fill="#0F172A" />
      <path
        d="M14 12H28C32.4183 12 36 15.5817 36 20C36 22.8 34.5 25.2 32.2 26.5C35 27.8 37 30.7 37 34C37 38.4183 33.4183 42 29 42H14V12Z"
        stroke="#3B82F6"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M14 26H28" stroke="#3B82F6" strokeWidth="3" />
      <path d="M22 17L28 17" stroke="#F59E0B" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="28" cy="26" r="3.5" fill="#10B981" />
      <path d="M26 35H30" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
};
