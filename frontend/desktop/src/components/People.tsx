import { useEffect, useState } from 'react';
import { people } from '../config/api';
import Card, { CardBody } from './ui/Card';
import Button from './ui/Button';
import Input from './ui/Input';
import Modal from './ui/Modal';
import Badge from './ui/Badge';
import { SkeletonCard } from './ui/Loading';
import { Search, Trash2, User, Grid, List, AlertTriangle } from 'lucide-react';

export default function People() {
  const [persons, setPersons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [personToDelete, setPersonToDelete] = useState<any>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchPeople();
  }, []);

  const fetchPeople = async () => {
    try {
      const res = await people.list();
      setPersons(res.data);
    } catch (err) {
      console.error('Failed to fetch people:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (person: any) => {
    setPersonToDelete(person);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!personToDelete) return;

    setIsDeleting(true);
    try {
      await people.delete(personToDelete.UserId);
      setPersons(persons.filter(p => p.UserId !== personToDelete.UserId));
      setDeleteModalOpen(false);
      setPersonToDelete(null);
    } catch (err) {
      console.error('Failed to delete person:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const filteredPersons = persons.filter(person =>
    person.Name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.UserId?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">People Management</h1>
          <p className="text-gray-400">Manage enrolled users and their facial data</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-gray-800 p-1 rounded-lg flex items-center border border-gray-700">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition-all ${viewMode === 'grid' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
            >
              <Grid size={20} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-all ${viewMode === 'list' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
            >
              <List size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <Input
          placeholder="Search by name or ID..."
          className="pl-10"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Content */}
      {filteredPersons.length === 0 ? (
        <div className="text-center py-12 bg-gray-800/30 rounded-xl border border-gray-700 border-dashed">
          <User size={48} className="mx-auto mb-4 text-gray-500" />
          <h3 className="text-xl font-medium text-white mb-1">No people found</h3>
          <p className="text-gray-400">
            {searchTerm ? 'Try adjusting your search terms' : 'Start by enrolling a new person'}
          </p>
        </div>
      ) : (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredPersons.map((person) => (
                <Card key={person.UserId} hover className="group relative overflow-hidden">
                  <CardBody className="p-0">
                    <div className="aspect-square bg-gray-800 relative">
                      {/* Placeholder for face image if available, or generic avatar */}
                      <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-gray-700 to-gray-800">
                        <User size={64} className="text-gray-500" />
                      </div>
                      {/* Overlay Actions */}
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 backdrop-blur-sm">
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleDeleteClick(person)}
                        >
                          <Trash2 size={16} />
                          Delete
                        </Button>
                      </div>
                    </div>
                    <div className="p-4">
                      <h3 className="font-bold text-white text-lg truncate">{person.Name || 'Unknown'}</h3>
                      <div className="flex items-center justify-between mt-2">
                        <Badge variant="info" size="sm">ID: {person.UserId}</Badge>
                      </div>
                    </div>
                  </CardBody>
                </Card>
              ))}
            </div>
          ) : (
            <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
              <table className="w-full text-left">
                <thead className="bg-gray-900/50 text-gray-400 text-sm uppercase">
                  <tr>
                    <th className="p-4 font-medium">User</th>
                    <th className="p-4 font-medium">ID</th>
                    <th className="p-4 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {filteredPersons.map((person) => (
                    <tr key={person.UserId} className="hover:bg-gray-700/50 transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center">
                            <User size={20} className="text-gray-400" />
                          </div>
                          <span className="font-medium text-white">{person.Name || 'Unknown'}</span>
                        </div>
                      </td>
                      <td className="p-4 text-gray-300">{person.UserId}</td>
                      <td className="p-4 text-right">
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => handleDeleteClick(person)}
                        >
                          <Trash2 size={16} />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Confirm Deletion"
        size="sm"
      >
        <div className="space-y-4">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={20} />
            <div>
              <h4 className="font-medium text-red-400">Warning</h4>
              <p className="text-sm text-red-300/80 mt-1">
                This action cannot be undone. This will permanently delete the user
                <span className="font-bold text-white"> {personToDelete?.Name} </span>
                and all associated facial data.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <Button
              variant="ghost"
              onClick={() => setDeleteModalOpen(false)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={confirmDelete}
              isLoading={isDeleting}
            >
              Delete User
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}