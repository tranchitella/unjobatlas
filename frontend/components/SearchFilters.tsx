import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Filters {
  query: string;
  organizations: string[];
  countries: string[];
  contractTypes: string[];
  positionLevels: string[];
  workArrangements: string[];
  isActive: boolean;
}

interface SearchFiltersProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

export function SearchFilters({ filters, onFiltersChange }: SearchFiltersProps) {
  const updateFilter = (key: keyof Filters, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const toggleArrayValue = (key: keyof Filters, value: string) => {
    const currentArray = filters[key] as string[];
    const newArray = currentArray.includes(value)
      ? currentArray.filter((v) => v !== value)
      : [...currentArray, value];
    updateFilter(key, newArray);
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Search Filters</h2>

      {/* Search Query */}
      <div className="mb-6">
        <label className="text-sm font-medium mb-2 block">Search</label>
        <Input
          type="text"
          placeholder="Search jobs..."
          value={filters.query}
          onChange={(e) => updateFilter("query", e.target.value)}
        />
      </div>

      <Separator className="my-4" />

      {/* Active Jobs Only */}
      <div className="mb-6">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="active"
            checked={filters.isActive}
            onCheckedChange={(checked) => updateFilter("isActive", checked)}
          />
          <label
            htmlFor="active"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Active jobs only
          </label>
        </div>
      </div>

      <Separator className="my-4" />

      {/* Organizations */}
      <div className="mb-6">
        <label className="text-sm font-medium mb-3 block">Organizations</label>
        <ScrollArea className="h-48">
          <div className="space-y-2">
            {["UNICEF", "WFP", "UNHCR", "WHO", "UNDP", "FAO", "UNESCO"].map(
              (org) => (
                <div key={org} className="flex items-center space-x-2">
                  <Checkbox
                    id={`org-${org}`}
                    checked={filters.organizations.includes(org)}
                    onCheckedChange={() => toggleArrayValue("organizations", org)}
                  />
                  <label
                    htmlFor={`org-${org}`}
                    className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {org}
                  </label>
                </div>
              )
            )}
          </div>
        </ScrollArea>
      </div>

      <Separator className="my-4" />

      {/* Countries */}
      <div className="mb-6">
        <label className="text-sm font-medium mb-3 block">Countries</label>
        <ScrollArea className="h-48">
          <div className="space-y-2">
            {[
              "Kenya",
              "Uganda",
              "Tanzania",
              "Ethiopia",
              "South Sudan",
              "Somalia",
              "Rwanda",
              "Switzerland",
              "United States",
            ].map((country) => (
              <div key={country} className="flex items-center space-x-2">
                <Checkbox
                  id={`country-${country}`}
                  checked={filters.countries.includes(country)}
                  onCheckedChange={() => toggleArrayValue("countries", country)}
                />
                <label
                  htmlFor={`country-${country}`}
                  className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {country}
                </label>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <Separator className="my-4" />

      {/* Contract Types */}
      <div className="mb-6">
        <label className="text-sm font-medium mb-3 block">Contract Type</label>
        <div className="space-y-2">
          {[
            "consultant",
            "temporary",
            "fixed_term",
            "internship",
            "volunteering",
          ].map((type) => (
            <div key={type} className="flex items-center space-x-2">
              <Checkbox
                id={`contract-${type}`}
                checked={filters.contractTypes.includes(type)}
                onCheckedChange={() => toggleArrayValue("contractTypes", type)}
              />
              <label
                htmlFor={`contract-${type}`}
                className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 capitalize"
              >
                {type.replace("_", " ")}
              </label>
            </div>
          ))}
        </div>
      </div>

      <Separator className="my-4" />

      {/* Position Levels */}
      <div className="mb-6">
        <label className="text-sm font-medium mb-3 block">Position Level</label>
        <ScrollArea className="h-48">
          <div className="space-y-2">
            {[
              "P-1",
              "P-2",
              "P-3",
              "P-4",
              "P-5",
              "NO-1",
              "NO-2",
              "NO-3",
              "G-5",
              "G-6",
              "G-7",
              "Consultancy",
              "Internship",
            ].map((level) => (
              <div key={level} className="flex items-center space-x-2">
                <Checkbox
                  id={`level-${level}`}
                  checked={filters.positionLevels.includes(level)}
                  onCheckedChange={() => toggleArrayValue("positionLevels", level)}
                />
                <label
                  htmlFor={`level-${level}`}
                  className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {level}
                </label>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <Separator className="my-4" />

      {/* Work Arrangement */}
      <div className="mb-6">
        <label className="text-sm font-medium mb-3 block">Work Arrangement</label>
        <div className="space-y-2">
          {["on-site", "remote", "hybrid"].map((arrangement) => (
            <div key={arrangement} className="flex items-center space-x-2">
              <Checkbox
                id={`work-${arrangement}`}
                checked={filters.workArrangements.includes(arrangement)}
                onCheckedChange={() =>
                  toggleArrayValue("workArrangements", arrangement)
                }
              />
              <label
                htmlFor={`work-${arrangement}`}
                className="text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 capitalize"
              >
                {arrangement}
              </label>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
