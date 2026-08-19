import React from 'react';
import { BookOpen, MoreVertical } from 'lucide-react';

interface ClassData {
  id: number;
  name: string;
  subject: string;
}

export default function PremiumClassCard({ cls }: { cls: ClassData }) {
  return (
    <div className="bg-white rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.05)] border border-gray-100 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 cursor-pointer relative overflow-hidden flex flex-col group h-48 hover:-translate-y-1">
      <div className="h-1.5 w-full bg-gradient-to-r from-[#0052CC] to-indigo-500 absolute top-0 left-0"></div>
      <div className="p-6 flex-grow flex flex-col justify-between mt-1">
        <div className="flex justify-between items-start">
          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-[#0052CC] group-hover:scale-110 transition-transform shadow-sm">
            <BookOpen size={24} strokeWidth={1.5} />
          </div>
          <button className="text-gray-400 hover:text-gray-700 transition-colors">
            <MoreVertical size={20} />
          </button>
        </div>
        <div className="mt-4">
          <h4 className="font-bold text-xl text-gray-900 line-clamp-1">{cls.name}</h4>
          <div className="flex items-center gap-3 mt-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#EAF2FF] text-[#0052CC]">
              {cls.subject}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
