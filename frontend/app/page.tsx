"use client";

import { useState } from "react";
import { SearchFilters } from "@/components/SearchFilters";
import { JobList } from "@/components/JobList";
import { JobDetails } from "@/components/JobDetails";

export default function Home() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    query: "",
    organizations: [] as string[],
    countries: [] as string[],
    contractTypes: [] as string[],
    positionLevels: [] as string[],
    workArrangements: [] as string[],
    isActive: true,
  });

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Column - Filters */}
      <div className="w-80 border-r bg-white overflow-y-auto">
        <SearchFilters filters={filters} onFiltersChange={setFilters} />
      </div>

      {/* Center Column - Job List */}
      <div className="flex-1 overflow-y-auto">
        <JobList
          filters={filters}
          selectedJobId={selectedJobId}
          onSelectJob={setSelectedJobId}
        />
      </div>

      {/* Right Column - Job Details */}
      <div className="w-[600px] border-l bg-white overflow-y-auto">
        <JobDetails jobId={selectedJobId} />
      </div>
    </div>
  );
}

